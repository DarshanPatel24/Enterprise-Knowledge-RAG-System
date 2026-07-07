"""Control Plane database engine and session management.

Provides a thin, configuration-driven factory around SQLAlchemy so the rest of
the engine depends on an abstraction rather than a concrete connection. The URL
is resolved from settings (Microsoft SQL Server in real environments; an
override URL such as SQLite is used for tests and local experimentation).
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from config.settings import ControlPlaneSettings
from domain.control_plane.models import Base, IngestionJob, IngestionSource


class ControlPlaneDatabase:
    """Owns the SQLAlchemy engine and session factory for the Control Plane."""

    def __init__(self, settings: ControlPlaneSettings, *, echo: bool = False) -> None:
        self._engine: Engine = create_engine(settings.sqlalchemy_url(), echo=echo, future=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    @property
    def engine(self) -> Engine:
        """Return the underlying SQLAlchemy engine."""
        return self._engine

    def create_all(self) -> None:
        """Create all Control Plane tables (development and test convenience).

        Production schema changes are managed through migrations, not this call.
        """
        Base.metadata.create_all(self._engine)

    def run_migrations(self) -> None:
        """Apply additive schema migrations idempotently.

        Safe to call on every startup: each migration checks whether the change
        is already present before issuing DDL. Supports both SQL Server and
        SQLite dialects. Silently skips if the assets table does not yet exist
        (create_all handles the initial schema for new deployments).
        """
        inspector = inspect(self._engine)
        dialect = self._engine.dialect.name

        # M-002: ingestion_jobs — durable async ingestion queue. Additive new
        # table; checkfirst makes this idempotent across SQL Server and SQLite.
        IngestionJob.__table__.create(bind=self._engine, checkfirst=True)

        # M-003: ingestion_sources — shared source-byte handoff for async jobs.
        IngestionSource.__table__.create(bind=self._engine, checkfirst=True)

        # M-001: assets.stage_metrics — per-stage processing metrics (JSON text).
        try:
            existing_columns = {c["name"] for c in inspector.get_columns("assets")}
        except Exception:  # noqa: BLE001 - table absent on first deploy; create_all handles it
            return
        if "stage_metrics" not in existing_columns:
            if dialect == "mssql":
                ddl = "ALTER TABLE assets ADD stage_metrics NVARCHAR(MAX) NULL"
            else:
                ddl = "ALTER TABLE assets ADD COLUMN stage_metrics TEXT"
            with self._engine.connect() as conn:
                conn.execute(text(ddl))
                conn.commit()

        # M-004: processing_state.processed/total — intra-stage progress counters.
        try:
            ps_columns = {c["name"] for c in inspector.get_columns("processing_state")}
        except Exception:  # noqa: BLE001 - table absent on first deploy; create_all handles it
            return
        int_type = "INT" if dialect == "mssql" else "INTEGER"
        for column in ("processed", "total"):
            if column not in ps_columns:
                if dialect == "mssql":
                    ddl = f"ALTER TABLE processing_state ADD {column} {int_type} NULL"
                else:
                    ddl = f"ALTER TABLE processing_state ADD COLUMN {column} {int_type}"
                with self._engine.connect() as conn:
                    conn.execute(text(ddl))
                    conn.commit()

    def drop_all(self) -> None:
        """Drop all Control Plane tables (test teardown convenience)."""
        Base.metadata.drop_all(self._engine)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Yield a transactional session, committing on success."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

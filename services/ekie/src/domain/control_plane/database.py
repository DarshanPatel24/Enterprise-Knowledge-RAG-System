"""Control Plane database engine and session management.

Provides a thin, configuration-driven factory around SQLAlchemy so the rest of
the engine depends on an abstraction rather than a concrete connection. The URL
is resolved from settings (Microsoft SQL Server in real environments; an
override URL such as SQLite is used for tests and local experimentation).
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import ControlPlaneSettings
from domain.control_plane.models import Base


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

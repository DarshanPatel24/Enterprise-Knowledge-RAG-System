"""Shared source-byte handoff for asynchronous ingestion jobs.

Async ingestion accepts the source bytes in the API process but executes the
pipeline in a separate worker process. The bytes are staged in the Control Plane
database (the shared source of truth) so the worker can load them regardless of
which process — or machine — runs it. This avoids relying on process-local
in-memory asset storage, which cannot cross process boundaries.
"""

from __future__ import annotations

from domain.control_plane import ControlPlaneDatabase, IngestionSource


class SourceStore:
    """Stage and retrieve raw ingestion source bytes via the Control Plane DB."""

    def __init__(self, db: ControlPlaneDatabase) -> None:
        self._db = db

    def store(self, tenant_id: str, document_id: str, data: bytes) -> None:
        """Persist (or replace) the source bytes for a document."""
        with self._db.session() as session:
            existing = (
                session.query(IngestionSource)
                .filter(
                    IngestionSource.tenant_id == tenant_id,
                    IngestionSource.document_id == document_id,
                )
                .first()
            )
            if existing is not None:
                existing.content = data
            else:
                session.add(
                    IngestionSource(
                        tenant_id=tenant_id,
                        document_id=document_id,
                        content=data,
                    )
                )

    def load(self, tenant_id: str, document_id: str) -> bytes | None:
        """Return the staged source bytes, or ``None`` if none are staged."""
        with self._db.session() as session:
            row = (
                session.query(IngestionSource)
                .filter(
                    IngestionSource.tenant_id == tenant_id,
                    IngestionSource.document_id == document_id,
                )
                .first()
            )
            return bytes(row.content) if row is not None else None

    def delete(self, tenant_id: str, document_id: str) -> None:
        """Remove staged source bytes once they are no longer needed."""
        with self._db.session() as session:
            session.query(IngestionSource).filter(
                IngestionSource.tenant_id == tenant_id,
                IngestionSource.document_id == document_id,
            ).delete()

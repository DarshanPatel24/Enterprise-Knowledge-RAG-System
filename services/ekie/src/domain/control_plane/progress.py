"""Cross-process stage progress reporting.

Long-running stages (notably embedding) process a document in batches. Because
generated assets are only written when a stage completes, mid-stage progress is
invisible to out-of-process observers such as the live monitor. This module lets
a stage publish incremental progress to the ``processing_state`` table so any
process reading the Control Plane can show "N of M chunks" style progress.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.control_plane.database import ControlPlaneDatabase
from domain.control_plane.models import ProcessingState, ProcessingStatus


@runtime_checkable
class ProgressReporter(Protocol):
    """Publishes incremental progress for a long-running pipeline stage."""

    def report(
        self, *, document_id: str, tenant_id: str, stage: str, processed: int, total: int
    ) -> None:
        """Record that ``processed`` of ``total`` units are done for a stage."""


class NullProgressReporter:
    """A no-op reporter for offline and test paths."""

    def report(
        self, *, document_id: str, tenant_id: str, stage: str, processed: int, total: int
    ) -> None:
        """Ignore the progress update."""
        return None


class ControlPlaneProgressReporter:
    """Persist stage progress to ``processing_state`` for cross-process visibility."""

    def __init__(self, db: ControlPlaneDatabase) -> None:
        self._db = db

    def report(
        self, *, document_id: str, tenant_id: str, stage: str, processed: int, total: int
    ) -> None:
        """Upsert the per-document stage progress record."""
        status = (
            ProcessingStatus.COMPLETED
            if total and processed >= total
            else ProcessingStatus.IN_PROGRESS
        )
        with self._db.session() as session:
            row = (
                session.query(ProcessingState)
                .filter(
                    ProcessingState.document_id == document_id,
                    ProcessingState.stage == stage,
                )
                .first()
            )
            if row is None:
                session.add(
                    ProcessingState(
                        document_id=document_id,
                        tenant_id=tenant_id,
                        stage=stage,
                        status=status,
                        processed=processed,
                        total=total,
                    )
                )
            else:
                row.tenant_id = tenant_id
                row.processed = processed
                row.total = total
                row.status = status

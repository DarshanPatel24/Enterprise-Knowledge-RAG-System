"""Tests for cross-process stage progress reporting."""

from __future__ import annotations

from domain.control_plane import (
    ControlPlaneDatabase,
    ProcessingState,
    ProcessingStatus,
)
from domain.control_plane.progress import ControlPlaneProgressReporter

_TENANT = "tenant-p"


def test_reporter_upserts_and_marks_in_progress(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    reporter = ControlPlaneProgressReporter(control_plane_db)

    reporter.report(
        document_id="doc-1", tenant_id=_TENANT, stage="embedding", processed=0, total=10
    )
    reporter.report(
        document_id="doc-1", tenant_id=_TENANT, stage="embedding", processed=4, total=10
    )

    with control_plane_db.session() as session:
        rows = session.query(ProcessingState).filter_by(document_id="doc-1").all()
        assert len(rows) == 1  # upsert, not insert-per-call
        row = rows[0]
        assert row.stage == "embedding"
        assert row.processed == 4
        assert row.total == 10
        assert row.status == ProcessingStatus.IN_PROGRESS


def test_reporter_marks_completed_when_done(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    reporter = ControlPlaneProgressReporter(control_plane_db)

    reporter.report(
        document_id="doc-2", tenant_id=_TENANT, stage="embedding", processed=10, total=10
    )

    with control_plane_db.session() as session:
        row = session.query(ProcessingState).filter_by(document_id="doc-2").one()
        assert row.processed == 10
        assert row.total == 10
        assert row.status == ProcessingStatus.COMPLETED

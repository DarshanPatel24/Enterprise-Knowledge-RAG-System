"""End-to-end pipeline validation tests (EKIE-S9-1)."""

from __future__ import annotations

from _validation_support import SOURCE, TENANT, build_harness, register_document

from domain.control_plane import ControlPlaneDatabase
from domain.orchestration import WorkflowStatus
from domain.validation import Severity


def test_completed_pipeline_passes_validation(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(control_plane_db)
    document_id = register_document(control_plane_db)

    result = harness.orchestrator.run(document_id, TENANT, source_bytes=SOURCE)
    assert result.status is WorkflowStatus.COMPLETED

    report = harness.validator.validate(result)
    assert report.passed, [f.message for f in report.errors]
    assert report.name == f"pipeline:{document_id}"


def test_validation_reports_missing_assets_for_unrun_document(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(control_plane_db)
    document_id = register_document(control_plane_db)

    result = harness.orchestrator.run(document_id, TENANT, source_bytes=SOURCE)
    # A validator pointed at a different (unpublished) document must fail.
    other_id = register_document(control_plane_db)
    from dataclasses import replace  # noqa: PLC0415 - local test-only import

    stale = replace(result, document_id=other_id)
    report = harness.validator.validate(stale)
    assert not report.passed
    assert any(f.severity is Severity.ERROR for f in report.findings)

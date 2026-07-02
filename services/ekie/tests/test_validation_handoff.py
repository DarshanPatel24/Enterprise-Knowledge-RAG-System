"""EKRE handoff readiness package tests (EKIE-S9-5)."""

from __future__ import annotations

import pytest
from _validation_support import SOURCE, TENANT, build_harness, register_document

from domain.control_plane import ControlPlaneDatabase
from domain.orchestration import StageName
from domain.validation import ValidationError, build_handoff_package
from domain.validation.failure import failing_stages


def test_handoff_package_built_for_published_document(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(control_plane_db)
    document_id = register_document(
        control_plane_db, classification="confidential", content_hash="abc123"
    )
    result = harness.orchestrator.run(document_id, TENANT, source_bytes=SOURCE)

    package = build_handoff_package(control_plane_db, harness.storage, result)

    assert package.document_id == document_id
    assert package.tenant_id == TENANT
    assert package.classification_clearance == "confidential"
    assert package.source_content_hash == "abc123"
    assert package.vector_count > 0
    assert package.chunk_count > 0
    assert package.dimension > 0
    assert package.validation_passed
    assert set(package.lineage_relations) == {
        "chunked_from_intelligence",
        "derived_from_markdown",
        "embedded_from_chunks",
        "published_from_embedding",
    }


def test_handoff_rejects_unpublished_document(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(
        control_plane_db, stages=failing_stages(StageName.PUBLISH)
    )
    document_id = register_document(control_plane_db)
    result = harness.orchestrator.run(document_id, TENANT, source_bytes=SOURCE)

    with pytest.raises(ValidationError):
        build_handoff_package(control_plane_db, harness.storage, result)

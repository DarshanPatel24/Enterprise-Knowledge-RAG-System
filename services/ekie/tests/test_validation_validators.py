"""Unit tests for individual pipeline validators (EKIE-S9-2)."""

from __future__ import annotations

from _validation_support import SOURCE, TENANT, build_harness, register_document

from domain.control_plane import ControlPlaneDatabase
from domain.validation import (
    validate_chunks,
    validate_embeddings,
    validate_lineage,
    validate_vectors,
    validate_workflow,
)
from domain.validation.assets import load_chunks, load_embedding, load_vectors


def test_validators_pass_on_real_assets(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(control_plane_db)
    document_id = register_document(control_plane_db)
    result = harness.orchestrator.run(document_id, TENANT, source_bytes=SOURCE)

    chunks = load_chunks(
        control_plane_db, harness.storage, document_id=document_id, tenant_id=TENANT
    )
    embedding = load_embedding(
        control_plane_db, harness.storage, document_id=document_id, tenant_id=TENANT
    )
    vectors = load_vectors(
        control_plane_db, harness.storage, document_id=document_id, tenant_id=TENANT
    )
    assert chunks is not None
    assert embedding is not None
    assert vectors is not None

    assert validate_workflow(result).passed
    assert validate_lineage(control_plane_db, document_id=document_id).passed
    assert validate_chunks(chunks).passed
    assert validate_embeddings(chunks, embedding).passed
    assert validate_vectors(embedding, vectors).passed


def test_validate_chunks_detects_count_mismatch(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(control_plane_db)
    document_id = register_document(control_plane_db)
    harness.orchestrator.run(document_id, TENANT, source_bytes=SOURCE)
    chunks = load_chunks(
        control_plane_db, harness.storage, document_id=document_id, tenant_id=TENANT
    )
    assert chunks is not None

    tampered = chunks.model_copy(update={"chunk_count": chunks.chunk_count + 1})
    report = validate_chunks(tampered)
    assert not report.passed
    assert any(f.check == "chunks.count" for f in report.errors)


def test_validate_embeddings_detects_uncovered_chunk(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(control_plane_db)
    document_id = register_document(control_plane_db)
    harness.orchestrator.run(document_id, TENANT, source_bytes=SOURCE)
    chunks = load_chunks(
        control_plane_db, harness.storage, document_id=document_id, tenant_id=TENANT
    )
    embedding = load_embedding(
        control_plane_db, harness.storage, document_id=document_id, tenant_id=TENANT
    )
    assert chunks is not None
    assert embedding is not None

    dropped = embedding.model_copy(update={"records": embedding.records[:-1]})
    report = validate_embeddings(chunks, dropped)
    assert not report.passed
    assert any(f.check == "embeddings.coverage" for f in report.errors)

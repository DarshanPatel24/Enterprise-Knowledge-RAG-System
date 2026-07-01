"""Unit tests for the required-field validation gate (EKIE-S6-4)."""

from domain.embedding import DistanceMetric
from domain.publishing import VectorMetadata, missing_required_fields


def _metadata(**overrides: object) -> VectorMetadata:
    base: dict[str, object] = {
        "document_id": "DOC-1",
        "chunk_id": "CHK-000001",
        "tenant_id": "tenant-a",
        "classification_clearance": "internal",
        "distance_metric": DistanceMetric.COSINE,
        "collection": "enterprise_documents",
        "embedding_model": "local-hash-256",
        "embedding_version": 1,
        "dimension": 256,
    }
    base.update(overrides)
    return VectorMetadata(**base)  # type: ignore[arg-type]


def test_complete_metadata_has_no_missing_fields() -> None:
    assert missing_required_fields(_metadata()) == []


def test_missing_tenant_is_detected() -> None:
    missing = missing_required_fields(_metadata(tenant_id=""))
    assert "tenant_id" in missing


def test_missing_classification_is_detected() -> None:
    missing = missing_required_fields(_metadata(classification_clearance=""))
    assert "classification_clearance" in missing


def test_non_positive_dimension_is_detected() -> None:
    missing = missing_required_fields(_metadata(dimension=0))
    assert "dimension" in missing


def test_non_positive_embedding_version_is_detected() -> None:
    missing = missing_required_fields(_metadata(embedding_version=0))
    assert "embedding_version" in missing

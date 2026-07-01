"""Unit tests for the in-memory vector provider and verification."""

import pytest

from domain.embedding import DistanceMetric
from domain.publishing import (
    CollectionSpec,
    InMemoryVectorProvider,
    PublishVerifier,
    VectorMetadata,
    VectorPoint,
    VectorProviderError,
    VerificationErrorType,
)


def _metadata(collection: str, chunk_id: str = "CHK-000001") -> VectorMetadata:
    return VectorMetadata(
        document_id="DOC-1",
        chunk_id=chunk_id,
        tenant_id="tenant-a",
        classification_clearance="internal",
        distance_metric=DistanceMetric.COSINE,
        collection=collection,
        embedding_model="local-hash-256",
        embedding_version=1,
        dimension=3,
    )


def _spec(name: str = "col", dimension: int = 3) -> CollectionSpec:
    return CollectionSpec(name=name, dimension=dimension, distance_metric="cosine")


def test_upsert_and_fetch_roundtrip() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(_spec())
    point = VectorPoint(vector_id="v1", values=[0.1, 0.2, 0.3], metadata=_metadata("col"))

    provider.upsert("col", [point])

    stored = provider.fetch("col", "v1")
    assert stored == point
    assert provider.count("col") == 1


def test_upsert_is_idempotent_by_vector_id() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(_spec())
    point = VectorPoint(vector_id="v1", values=[0.1, 0.2, 0.3], metadata=_metadata("col"))

    provider.upsert("col", [point])
    provider.upsert("col", [point])

    assert provider.count("col") == 1


def test_ensure_collection_rejects_schema_conflict() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(_spec(dimension=3))

    with pytest.raises(VectorProviderError):
        provider.ensure_collection(_spec(dimension=4))


def test_upsert_rejects_wrong_dimension() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(_spec(dimension=3))
    bad = VectorPoint(vector_id="v1", values=[0.1, 0.2], metadata=_metadata("col"))

    with pytest.raises(VectorProviderError):
        provider.upsert("col", [bad])


def test_delete_removes_vectors() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(_spec())
    point = VectorPoint(vector_id="v1", values=[0.1, 0.2, 0.3], metadata=_metadata("col"))
    provider.upsert("col", [point])

    provider.delete("col", ["v1"])

    assert provider.count("col") == 0


def test_verification_passes_for_published_points() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(_spec())
    point = VectorPoint(vector_id="v1", values=[0.1, 0.2, 0.3], metadata=_metadata("col"))
    provider.upsert("col", [point])

    report = PublishVerifier(provider).verify("col", [point])

    assert report.verified is True
    assert report.verified_count == 1


def test_verification_detects_missing_vector() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(_spec())
    point = VectorPoint(vector_id="v1", values=[0.1, 0.2, 0.3], metadata=_metadata("col"))

    report = PublishVerifier(provider).verify("col", [point])

    assert report.verified is False
    assert VerificationErrorType.MISSING_VECTOR in report.errors

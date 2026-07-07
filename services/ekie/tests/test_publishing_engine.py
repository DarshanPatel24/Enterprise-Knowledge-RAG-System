"""Integration tests for the vector publishing engine over the full chain."""

import pytest

from domain.chunking import ChunkingEngine, ChunkingPolicy
from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Lineage,
    Repository,
    RepositoryStatus,
)
from domain.embedding import EmbeddingEngine, EmbeddingPolicy
from domain.intelligence import DocumentIntelligenceEngine, IntelligencePolicy
from domain.publishing import (
    PublishError,
    PublishErrorType,
    PublishingPolicy,
    SyncState,
    VectorPublishingEngine,
    default_provider_registry,
)
from domain.storage import InMemoryAssetStorage
from domain.transformation import TransformationPipeline, TransformationPolicy

_MARKDOWN = """# Equipment Maintenance

Overview of the maintenance workflow for the pump station.

## Safety

Warning: disconnect power before service.

## Inspection

1. Inspect the seals.
2. Check the pressure gauge.

## Status

| Equipment | Status | Next Inspection |
| --- | --- | --- |
| Pump | OK | 2024-06-01 |
| Valve | OK | 2024-07-01 |
"""


def _seed_document(db: ControlPlaneDatabase) -> str:
    with db.session() as session:
        repo = Repository(
            tenant_id="tenant-a",
            name="repo",
            source_type="local_fs",
            uri="local://repo",
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repo)
        session.flush()
        document = Document(
            repository_id=repo.id,
            tenant_id="tenant-a",
            source_path="docs/maint.md",
            content_hash="hash-maint",
            classification_clearance="internal",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


def _prepare(
    db: ControlPlaneDatabase, *, embed: bool = True
) -> tuple[str, InMemoryAssetStorage]:
    document_id = _seed_document(db)
    storage = InMemoryAssetStorage()
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    DocumentIntelligenceEngine(db, storage, IntelligencePolicy()).enrich(
        document_id, "tenant-a"
    )
    ChunkingEngine(db, storage, ChunkingPolicy()).chunk(document_id, "tenant-a")
    if embed:
        EmbeddingEngine(db, storage, EmbeddingPolicy()).embed(document_id, "tenant-a")
    return document_id, storage


def test_publish_creates_verified_vector_asset_with_lineage(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = VectorPublishingEngine(
        control_plane_db, storage, PublishingPolicy()
    )

    result = engine.publish(document_id, "tenant-a")

    assert result.created is True
    assert result.version == 1
    assert result.collection == "enterprise_documents"
    assert result.provider == "local"
    assert result.dimension == 256
    assert result.vector_count >= 3
    assert result.verified_count == result.vector_count
    published = result.published_vector_set
    assert all(record.state is SyncState.VERIFIED for record in published.records)
    # Every vector carries complete mandatory governance metadata.
    assert all(record.chunk_content_hash for record in published.records)

    with control_plane_db.session() as session:
        vector_asset = (
            session.query(Asset).filter(Asset.asset_type == AssetType.VECTOR).one()
        )
        embedding_asset = (
            session.query(Asset).filter(Asset.asset_type == AssetType.EMBEDDING).one()
        )
        lineage = (
            session.query(Lineage).filter(Lineage.asset_id == vector_asset.id).one()
        )
        assert lineage.parent_asset_id == embedding_asset.id
        assert lineage.relation == "published_from_embedding"


def test_published_vectors_carry_mandatory_metadata(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    registry = default_provider_registry()
    engine = VectorPublishingEngine(
        control_plane_db, storage, PublishingPolicy(), provider_registry=registry
    )

    result = engine.publish(document_id, "tenant-a")

    provider = registry.get("local")
    for record in result.published_vector_set.records:
        stored = provider.fetch("enterprise_documents", record.vector_id)
        assert stored is not None
        meta = stored.metadata
        assert meta.document_id == document_id
        assert meta.tenant_id == "tenant-a"
        assert meta.classification_clearance == "internal"
        assert meta.collection == "enterprise_documents"
        assert meta.embedding_model == "local-hash-256"
        assert meta.dimension == 256
        # Enrichment from the chunk set.
        assert meta.language == "en"


def test_publishing_is_idempotent(control_plane_db: ControlPlaneDatabase) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = VectorPublishingEngine(
        control_plane_db, storage, PublishingPolicy()
    )

    first = engine.publish(document_id, "tenant-a")
    second = engine.publish(document_id, "tenant-a")

    assert first.content_hash == second.content_hash
    assert second.created is False
    assert second.version == first.version
    with control_plane_db.session() as session:
        count = (
            session.query(Asset).filter(Asset.asset_type == AssetType.VECTOR).count()
        )
        assert count == 1


def test_publishing_respects_batch_size(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = VectorPublishingEngine(
        control_plane_db, storage, PublishingPolicy(batch_size=1)
    )

    result = engine.publish(document_id, "tenant-a")

    assert result.batch_count == result.vector_count


def test_publishing_reports_incremental_progress(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    calls: list[tuple[str, int, int]] = []

    class _SpyReporter:
        def report(
            self, *, document_id: str, tenant_id: str, stage: str, processed: int, total: int
        ) -> None:
            calls.append((stage, processed, total))

    engine = VectorPublishingEngine(
        control_plane_db,
        storage,
        PublishingPolicy(batch_size=1),
        progress_reporter=_SpyReporter(),
    )

    result = engine.publish(document_id, "tenant-a")
    total = result.vector_count

    assert calls[0] == ("vector", 0, total)
    assert calls[-1] == ("vector", total, total)
    processed_seq = [processed for _, processed, _ in calls]
    assert processed_seq == sorted(processed_seq)
    assert all(stage == "vector" and reported_total == total for stage, _, reported_total in calls)


def test_publish_requires_embedding_asset(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db, embed=False)
    engine = VectorPublishingEngine(
        control_plane_db, storage, PublishingPolicy()
    )

    with pytest.raises(PublishError) as excinfo:
        engine.publish(document_id, "tenant-a")
    assert excinfo.value.error_type is PublishErrorType.MISSING_EMBEDDING


def test_publish_fails_when_collection_missing_and_creation_disabled(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = VectorPublishingEngine(
        control_plane_db,
        storage,
        PublishingPolicy(create_missing_collections=False),
    )

    with pytest.raises(PublishError) as excinfo:
        engine.publish(document_id, "tenant-a")
    assert excinfo.value.error_type is PublishErrorType.COLLECTION_UNAVAILABLE


def test_publish_unknown_document_raises_not_found(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    engine = VectorPublishingEngine(
        control_plane_db, InMemoryAssetStorage(), PublishingPolicy()
    )

    with pytest.raises(PublishError) as excinfo:
        engine.publish("missing-id", "tenant-a")
    assert excinfo.value.error_type is PublishErrorType.NOT_FOUND

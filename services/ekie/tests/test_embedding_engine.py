"""Integration tests for the embedding engine over the full ingestion chain."""

import math

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
from domain.embedding import (
    DistanceMetric,
    EmbeddingEngine,
    EmbeddingError,
    EmbeddingErrorType,
    EmbeddingPolicy,
)
from domain.intelligence import DocumentIntelligenceEngine, IntelligencePolicy
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
    db: ControlPlaneDatabase, *, chunk: bool = True
) -> tuple[str, InMemoryAssetStorage]:
    document_id = _seed_document(db)
    storage = InMemoryAssetStorage()
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    DocumentIntelligenceEngine(db, storage, IntelligencePolicy()).enrich(
        document_id, "tenant-a"
    )
    if chunk:
        ChunkingEngine(db, storage, ChunkingPolicy()).chunk(document_id, "tenant-a")
    return document_id, storage


def test_embed_creates_versioned_asset_with_lineage(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = EmbeddingEngine(control_plane_db, storage, EmbeddingPolicy())

    result = engine.embed(document_id, "tenant-a")

    assert result.created is True
    assert result.version == 1
    assert result.dimension == 256
    assert result.provider == "local"
    assert result.embedding_document.distance_metric is DistanceMetric.COSINE
    assert result.embedding_document.embedding_count >= 3
    assert result.total_tokens > 0
    records = result.embedding_document.records
    assert all(len(record.values) == 256 for record in records)
    assert all(record.embedding_id.startswith("EMB-") for record in records)
    # Every record links back to a chunk content hash for governance.
    assert all(record.chunk_content_hash for record in records)
    # Normalized vectors have unit magnitude.
    magnitude = math.sqrt(sum(value * value for value in records[0].values))
    assert math.isclose(magnitude, 1.0, rel_tol=1e-9)

    with control_plane_db.session() as session:
        embedding_asset = (
            session.query(Asset).filter(Asset.asset_type == AssetType.EMBEDDING).one()
        )
        chunk_asset = (
            session.query(Asset).filter(Asset.asset_type == AssetType.CHUNKS).one()
        )
        lineage = (
            session.query(Lineage).filter(Lineage.asset_id == embedding_asset.id).one()
        )
        assert lineage.parent_asset_id == chunk_asset.id
        assert lineage.relation == "embedded_from_chunks"


def test_embedding_is_idempotent(control_plane_db: ControlPlaneDatabase) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = EmbeddingEngine(control_plane_db, storage, EmbeddingPolicy())

    first = engine.embed(document_id, "tenant-a")
    second = engine.embed(document_id, "tenant-a")

    assert first.content_hash == second.content_hash
    assert second.created is False
    assert second.version == first.version
    with control_plane_db.session() as session:
        count = (
            session.query(Asset).filter(Asset.asset_type == AssetType.EMBEDDING).count()
        )
        assert count == 1


def test_embedding_respects_batch_size(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = EmbeddingEngine(
        control_plane_db, storage, EmbeddingPolicy(batch_size=1)
    )

    result = engine.embed(document_id, "tenant-a")

    assert result.batch_count == result.embedding_document.embedding_count


def test_embedding_reports_incremental_progress(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    calls: list[tuple[str, int, int]] = []

    class _SpyReporter:
        def report(
            self, *, document_id: str, tenant_id: str, stage: str, processed: int, total: int
        ) -> None:
            calls.append((stage, processed, total))

    engine = EmbeddingEngine(
        control_plane_db,
        storage,
        EmbeddingPolicy(batch_size=1),
        progress_reporter=_SpyReporter(),
    )

    result = engine.embed(document_id, "tenant-a")
    total = result.embedding_document.embedding_count

    assert calls[0] == ("embedding", 0, total)
    assert calls[-1] == ("embedding", total, total)
    processed_seq = [processed for _, processed, _ in calls]
    assert processed_seq == sorted(processed_seq)
    assert all(stage == "embedding" and reported_total == total for stage, _, reported_total in calls)


def test_embedding_requires_chunk_asset(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db, chunk=False)
    engine = EmbeddingEngine(control_plane_db, storage, EmbeddingPolicy())

    with pytest.raises(EmbeddingError) as excinfo:
        engine.embed(document_id, "tenant-a")
    assert excinfo.value.error_type is EmbeddingErrorType.MISSING_CHUNKS


def test_embedding_enforces_token_limit(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = EmbeddingEngine(
        control_plane_db, storage, EmbeddingPolicy(max_input_tokens=1)
    )

    with pytest.raises(EmbeddingError) as excinfo:
        engine.embed(document_id, "tenant-a")
    assert excinfo.value.error_type is EmbeddingErrorType.TOKEN_LIMIT_EXCEEDED


def test_embed_unknown_document_raises_not_found(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    engine = EmbeddingEngine(
        control_plane_db, InMemoryAssetStorage(), EmbeddingPolicy()
    )

    with pytest.raises(EmbeddingError) as excinfo:
        engine.embed("missing-id", "tenant-a")
    assert excinfo.value.error_type is EmbeddingErrorType.NOT_FOUND

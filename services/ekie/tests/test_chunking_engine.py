"""Integration tests for the chunking engine over the full ingestion chain."""

import pytest

from domain.chunking import (
    ChunkingEngine,
    ChunkingError,
    ChunkingErrorType,
    ChunkingPolicy,
)
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


def _prepare(db: ControlPlaneDatabase) -> tuple[str, InMemoryAssetStorage]:
    document_id = _seed_document(db)
    storage = InMemoryAssetStorage()
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    DocumentIntelligenceEngine(db, storage, IntelligencePolicy()).enrich(
        document_id, "tenant-a"
    )
    return document_id, storage


def test_chunk_creates_versioned_asset_with_lineage(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = ChunkingEngine(control_plane_db, storage, ChunkingPolicy())

    result = engine.chunk(document_id, "tenant-a")

    assert result.created is True
    assert result.version == 1
    assert result.chunk_document.chunk_count >= 3
    # Table stays intact in a single chunk.
    table_chunks = [c for c in result.chunk_document.chunks if c.metadata.contains_table]
    assert len(table_chunks) == 1
    assert "| Equipment | Status | Next Inspection |" in table_chunks[0].content
    # Governance metadata inherited from the document.
    assert all(c.metadata.classification == "internal" for c in result.chunk_document.chunks)
    assert all(c.metadata.chunk_id.startswith("CHK-") for c in result.chunk_document.chunks)

    with control_plane_db.session() as session:
        chunk_asset = (
            session.query(Asset).filter(Asset.asset_type == AssetType.CHUNKS).one()
        )
        intelligence_asset = (
            session.query(Asset).filter(Asset.asset_type == AssetType.INTELLIGENCE).one()
        )
        lineage = (
            session.query(Lineage).filter(Lineage.asset_id == chunk_asset.id).one()
        )
        assert lineage.parent_asset_id == intelligence_asset.id
        assert lineage.relation == "chunked_from_intelligence"


def test_chunking_is_idempotent(control_plane_db: ControlPlaneDatabase) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = ChunkingEngine(control_plane_db, storage, ChunkingPolicy())

    first = engine.chunk(document_id, "tenant-a")
    second = engine.chunk(document_id, "tenant-a")

    assert first.content_hash == second.content_hash
    assert second.created is False
    assert second.version == first.version
    with control_plane_db.session() as session:
        count = (
            session.query(Asset).filter(Asset.asset_type == AssetType.CHUNKS).count()
        )
        assert count == 1


def test_chunk_requires_intelligence_asset(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _seed_document(control_plane_db)
    storage = InMemoryAssetStorage()
    TransformationPipeline(control_plane_db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    engine = ChunkingEngine(control_plane_db, storage, ChunkingPolicy())
    with pytest.raises(ChunkingError) as excinfo:
        engine.chunk(document_id, "tenant-a")
    assert excinfo.value.error_type is ChunkingErrorType.MISSING_INTELLIGENCE


def test_chunk_unknown_document_raises_not_found(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    engine = ChunkingEngine(
        control_plane_db, InMemoryAssetStorage(), ChunkingPolicy()
    )
    with pytest.raises(ChunkingError) as excinfo:
        engine.chunk("missing-id", "tenant-a")
    assert excinfo.value.error_type is ChunkingErrorType.NOT_FOUND

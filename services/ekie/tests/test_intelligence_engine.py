"""Integration tests for the document intelligence engine."""

import pytest

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
from domain.intelligence import (
    DocumentIntelligenceEngine,
    IntelligenceError,
    IntelligenceErrorType,
    IntelligencePolicy,
)
from domain.storage import InMemoryAssetStorage
from domain.transformation import TransformationPipeline, TransformationPolicy

_MARKDOWN = """# Maintenance Procedure

Follow this procedure carefully.

## Steps

1. Stop the pump.
2. Drain the reservoir.

## Data

| Part | Qty | Date |
| --- | --- | --- |
| ABC-1 | 12 | 2024-01-02 |
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
            source_path="docs/proc.md",
            content_hash="hash-proc",
            classification_clearance="internal",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


def _prepare(
    db: ControlPlaneDatabase,
) -> tuple[str, InMemoryAssetStorage]:
    document_id = _seed_document(db)
    storage = InMemoryAssetStorage()
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    return document_id, storage


def test_enrich_creates_intelligence_asset_with_lineage(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = DocumentIntelligenceEngine(
        control_plane_db, storage, IntelligencePolicy()
    )

    result = engine.enrich(document_id, "tenant-a")

    assert result.created is True
    assert result.version == 1
    assert result.report.classification.value in {"procedure", "general", "maintenance_guide"}
    assert result.report.semantic_metadata.section_count == 3
    assert len(result.report.tables) == 1

    with control_plane_db.session() as session:
        asset = (
            session.query(Asset)
            .filter(Asset.asset_type == AssetType.INTELLIGENCE)
            .one()
        )
        assert asset.version == 1
        markdown_asset = (
            session.query(Asset)
            .filter(Asset.asset_type == AssetType.MARKDOWN)
            .one()
        )
        lineage = session.query(Lineage).filter(Lineage.asset_id == asset.id).one()
        assert lineage.parent_asset_id == markdown_asset.id


def test_enrich_is_idempotent(control_plane_db: ControlPlaneDatabase) -> None:
    document_id, storage = _prepare(control_plane_db)
    engine = DocumentIntelligenceEngine(
        control_plane_db, storage, IntelligencePolicy()
    )

    first = engine.enrich(document_id, "tenant-a")
    second = engine.enrich(document_id, "tenant-a")

    assert first.content_hash == second.content_hash
    assert second.created is False
    assert second.version == first.version
    with control_plane_db.session() as session:
        count = (
            session.query(Asset)
            .filter(Asset.asset_type == AssetType.INTELLIGENCE)
            .count()
        )
        assert count == 1


def test_enrich_requires_markdown_asset(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _seed_document(control_plane_db)
    engine = DocumentIntelligenceEngine(
        control_plane_db, InMemoryAssetStorage(), IntelligencePolicy()
    )
    with pytest.raises(IntelligenceError) as excinfo:
        engine.enrich(document_id, "tenant-a")
    assert excinfo.value.error_type is IntelligenceErrorType.MISSING_MARKDOWN


def test_enrich_unknown_document_raises_not_found(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    engine = DocumentIntelligenceEngine(
        control_plane_db, InMemoryAssetStorage(), IntelligencePolicy()
    )
    with pytest.raises(IntelligenceError) as excinfo:
        engine.enrich("missing-id", "tenant-a")
    assert excinfo.value.error_type is IntelligenceErrorType.NOT_FOUND

"""Tests for the opt-in recursive character chunking strategy.

Recursive chunking is additive and only active when selected via
``EKIE_CHUNKING__DEFAULT_STRATEGY=recursive``; semantic remains the default.
These tests verify the strategy in isolation and end to end without changing
the behavior of the existing strategies.
"""

import importlib.util

import pytest

from domain.chunking import (
    ChunkingContext,
    ChunkingEngine,
    ChunkingError,
    ChunkingErrorType,
    ChunkingPolicy,
    ChunkStrategy,
    RecursiveCharacterChunkStrategy,
    SectionView,
    default_registry,
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
from domain.intelligence import (
    BlockType,
    DocumentIntelligenceEngine,
    IntelligencePolicy,
    MarkdownBlock,
)
from domain.storage import InMemoryAssetStorage
from domain.transformation import TransformationPipeline, TransformationPolicy

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("langchain_text_splitters") is None,
    reason="langchain-text-splitters is not installed",
)


def _paragraph(text: str, section_id: str) -> MarkdownBlock:
    return MarkdownBlock(block_type=BlockType.PARAGRAPH, text=text, section_id=section_id)


def _context(blocks: list[MarkdownBlock], *, contains_table: bool = False) -> ChunkingContext:
    section = SectionView(
        section_id="SEC-1",
        title="Safety",
        level=2,
        breadcrumb="Maintenance > Safety",
        blocks=blocks,
        contains_table=contains_table,
    )
    return ChunkingContext(
        document_id="DOC-1",
        markdown_version=1,
        language="en",
        classification="procedure",
        quality_score=95,
        sections=[section],
    )


def test_registry_selects_recursive_strategy() -> None:
    plugin = default_registry().select(ChunkStrategy.RECURSIVE)
    assert isinstance(plugin, RecursiveCharacterChunkStrategy)


def test_recursive_splits_long_section_preserving_metadata() -> None:
    words = " ".join(f"word{i}" for i in range(200))
    context = _context([_paragraph(words, "SEC-1")])
    policy = ChunkingPolicy(
        default_strategy=ChunkStrategy.RECURSIVE,
        recursive_chunk_size=120,
        recursive_chunk_overlap=30,
        include_breadcrumb_context=False,
    )

    drafts = RecursiveCharacterChunkStrategy().generate(context, policy)

    assert len(drafts) > 1
    assert all(d.section_id == "SEC-1" for d in drafts)
    assert all(d.section_title == "Safety" for d in drafts)
    assert all(d.breadcrumb == "Maintenance > Safety" for d in drafts)
    assert all(d.heading_level == 2 for d in drafts)


def test_recursive_chunks_overlap() -> None:
    words = " ".join(f"word{i}" for i in range(200))
    context = _context([_paragraph(words, "SEC-1")])
    policy = ChunkingPolicy(
        default_strategy=ChunkStrategy.RECURSIVE,
        recursive_chunk_size=120,
        recursive_chunk_overlap=40,
        include_breadcrumb_context=False,
    )

    drafts = RecursiveCharacterChunkStrategy().generate(context, policy)

    # Consecutive chunks should share at least one overlapping token.
    first_words = set(drafts[0].content.split())
    second_words = set(drafts[1].content.split())
    assert first_words & second_words


def test_recursive_small_section_single_chunk() -> None:
    context = _context([_paragraph("disconnect power before service", "SEC-1")])
    policy = ChunkingPolicy(
        default_strategy=ChunkStrategy.RECURSIVE,
        recursive_chunk_size=1000,
        recursive_chunk_overlap=100,
        include_breadcrumb_context=False,
    )

    drafts = RecursiveCharacterChunkStrategy().generate(context, policy)

    assert len(drafts) == 1
    assert "disconnect power before service" in drafts[0].content


def test_recursive_includes_breadcrumb_context() -> None:
    context = _context([_paragraph("some maintenance content", "SEC-1")])
    policy = ChunkingPolicy(
        default_strategy=ChunkStrategy.RECURSIVE, include_breadcrumb_context=True
    )

    drafts = RecursiveCharacterChunkStrategy().generate(context, policy)

    assert all("> Context: Maintenance > Safety" in d.content for d in drafts)


def test_recursive_overlap_must_be_smaller_than_size() -> None:
    context = _context([_paragraph("content", "SEC-1")])
    policy = ChunkingPolicy(
        default_strategy=ChunkStrategy.RECURSIVE,
        recursive_chunk_size=100,
        recursive_chunk_overlap=100,
    )

    with pytest.raises(ChunkingError) as exc_info:
        RecursiveCharacterChunkStrategy().generate(context, policy)
    assert exc_info.value.error_type is ChunkingErrorType.VALIDATION_FAILURE


_MARKDOWN = """# Equipment Maintenance

Overview of the maintenance workflow for the pump station.

## Safety

Warning: disconnect power before service.

## Inspection

1. Inspect the seals.
2. Check the pressure gauge.
"""


def _prepare(db: ControlPlaneDatabase) -> tuple[str, InMemoryAssetStorage]:
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
        document_id = document.id
    storage = InMemoryAssetStorage()
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    DocumentIntelligenceEngine(db, storage, IntelligencePolicy()).enrich(
        document_id, "tenant-a"
    )
    return document_id, storage


def test_recursive_chunking_end_to_end(control_plane_db: ControlPlaneDatabase) -> None:
    document_id, storage = _prepare(control_plane_db)
    policy = ChunkingPolicy(default_strategy=ChunkStrategy.RECURSIVE)
    engine = ChunkingEngine(control_plane_db, storage, policy)

    result = engine.chunk(document_id, "tenant-a")

    assert result.created is True
    assert result.chunk_document.chunk_count >= 1
    assert result.chunk_document.strategy is ChunkStrategy.RECURSIVE
    assert all(
        c.metadata.chunk_strategy is ChunkStrategy.RECURSIVE
        for c in result.chunk_document.chunks
    )
    assert all(c.metadata.chunk_id.startswith("CHK-") for c in result.chunk_document.chunks)
    assert all(c.metadata.classification == "internal" for c in result.chunk_document.chunks)

    with control_plane_db.session() as session:
        chunk_asset = (
            session.query(Asset).filter(Asset.asset_type == AssetType.CHUNKS).one()
        )
        lineage = session.query(Lineage).filter(Lineage.asset_id == chunk_asset.id).one()
        assert lineage.relation == "chunked_from_intelligence"


def test_recursive_chunking_is_idempotent(control_plane_db: ControlPlaneDatabase) -> None:
    document_id, storage = _prepare(control_plane_db)
    policy = ChunkingPolicy(default_strategy=ChunkStrategy.RECURSIVE)
    engine = ChunkingEngine(control_plane_db, storage, policy)

    first = engine.chunk(document_id, "tenant-a")
    second = engine.chunk(document_id, "tenant-a")

    assert first.content_hash == second.content_hash
    assert second.created is False
    assert second.version == first.version

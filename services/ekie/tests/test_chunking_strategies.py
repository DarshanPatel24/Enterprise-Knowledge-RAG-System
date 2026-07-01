"""Unit tests for chunk strategies operating on a manual context."""

from domain.chunking import (
    ChunkingContext,
    ChunkingPolicy,
    SectionView,
    SemanticChunkStrategy,
    TokenWindowChunkStrategy,
)
from domain.chunking.strategies.base import ChunkDraft
from domain.intelligence import BlockType, MarkdownBlock


def _heading(text: str, level: int, section_id: str) -> MarkdownBlock:
    return MarkdownBlock(
        block_type=BlockType.HEADING, text=text, level=level, section_id=section_id
    )


def _paragraph(text: str, section_id: str) -> MarkdownBlock:
    return MarkdownBlock(block_type=BlockType.PARAGRAPH, text=text, section_id=section_id)


def _table(section_id: str) -> MarkdownBlock:
    rows = [["Part", "Status"], ["Pump", "OK"], ["Valve", "OK"]]
    return MarkdownBlock(
        block_type=BlockType.TABLE, text="", section_id=section_id, table_rows=rows
    )


def _context() -> ChunkingContext:
    section = SectionView(
        section_id="SEC-1",
        title="Safety",
        level=2,
        breadcrumb="Maintenance > Safety",
        blocks=[
            _heading("Safety", 2, "SEC-1"),
            _paragraph("Always disconnect power before service.", "SEC-1"),
            _table("SEC-1"),
        ],
        contains_table=True,
    )
    return ChunkingContext(
        document_id="DOC-1",
        markdown_version=1,
        language="en",
        classification="procedure",
        quality_score=95,
        sections=[section],
    )


def test_semantic_keeps_table_as_isolated_chunk() -> None:
    drafts = SemanticChunkStrategy().generate(_context(), ChunkingPolicy())
    table_drafts = [d for d in drafts if d.contains_table]
    assert len(table_drafts) == 1
    # The table chunk must not merge the surrounding paragraph text.
    assert "disconnect power" not in table_drafts[0].content
    assert "| Part | Status |" in table_drafts[0].content


def test_semantic_prepends_breadcrumb_context() -> None:
    drafts = SemanticChunkStrategy().generate(_context(), ChunkingPolicy())
    assert all(d.breadcrumb == "Maintenance > Safety" for d in drafts)
    assert all("> Context: Maintenance > Safety" in d.content for d in drafts)


def test_semantic_groups_small_paragraphs_within_budget() -> None:
    section = SectionView(
        section_id="SEC-1",
        title="Intro",
        level=1,
        breadcrumb="Intro",
        blocks=[
            _heading("Intro", 1, "SEC-1"),
            _paragraph("one two three", "SEC-1"),
            _paragraph("four five six", "SEC-1"),
        ],
    )
    context = ChunkingContext(
        document_id="DOC-1",
        markdown_version=1,
        language="en",
        classification="general",
        quality_score=90,
        sections=[section],
    )
    drafts = SemanticChunkStrategy().generate(context, ChunkingPolicy())
    assert len(drafts) == 1
    assert "one two three" in drafts[0].content
    assert "four five six" in drafts[0].content


def test_semantic_respects_target_budget() -> None:
    blocks = [_heading("Intro", 1, "SEC-1")]
    blocks += [_paragraph(f"word{i} more text here now", "SEC-1") for i in range(6)]
    section = SectionView(
        section_id="SEC-1",
        title="Intro",
        level=1,
        breadcrumb="Intro",
        blocks=blocks,
    )
    context = ChunkingContext(
        document_id="DOC-1",
        markdown_version=1,
        language="en",
        classification="general",
        quality_score=90,
        sections=[section],
    )
    policy = ChunkingPolicy(target_token_budget=12, include_breadcrumb_context=False)
    drafts = SemanticChunkStrategy().generate(context, policy)
    assert len(drafts) > 1
    assert all(isinstance(d, ChunkDraft) for d in drafts)


def test_token_strategy_windows_within_section() -> None:
    blocks = [_paragraph(f"token{i} filler words go here", "SEC-1") for i in range(8)]
    section = SectionView(
        section_id="SEC-1",
        title="Data",
        level=1,
        breadcrumb="Data",
        blocks=blocks,
    )
    context = ChunkingContext(
        document_id="DOC-1",
        markdown_version=1,
        language="en",
        classification="general",
        quality_score=90,
        sections=[section],
    )
    policy = ChunkingPolicy(target_token_budget=15, include_breadcrumb_context=False)
    drafts = TokenWindowChunkStrategy().generate(context, policy)
    assert len(drafts) >= 2
    assert all(d.section_id == "SEC-1" for d in drafts)

"""Structural boundary detection and chunking context assembly (handbook 9.8).

Combines the parsed Markdown block stream with the Document Intelligence report
to produce section-scoped views. Sections are the primary semantic boundaries;
strategies apply finer boundaries (tables, code, notes) within each view.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.intelligence import (
    AnalyzedDocument,
    BlockType,
    DocumentIntelligenceReport,
    MarkdownBlock,
    SectionNode,
)

_PREAMBLE_TITLE = "Introduction"


@dataclass(frozen=True)
class SectionView:
    """A section boundary with its blocks and inherited intelligence flags."""

    section_id: str | None
    title: str
    level: int
    breadcrumb: str
    blocks: list[MarkdownBlock] = field(default_factory=list)
    contains_table: bool = False
    contains_code: bool = False
    contains_image: bool = False


@dataclass(frozen=True)
class ChunkingContext:
    """All inputs a chunk strategy needs to generate chunks for a document."""

    document_id: str
    markdown_version: int
    language: str
    classification: str
    quality_score: int
    sections: list[SectionView] = field(default_factory=list)


def _breadcrumbs(structure: list[SectionNode]) -> dict[str, str]:
    nodes = {node.section_id: node for node in structure}
    trails: dict[str, str] = {}
    for node in structure:
        titles = [node.title]
        parent_id = node.parent_id
        while parent_id is not None and parent_id in nodes:
            parent = nodes[parent_id]
            titles.append(parent.title)
            parent_id = parent.parent_id
        trails[node.section_id] = " > ".join(reversed(titles))
    return trails


def build_context(
    report: DocumentIntelligenceReport, analyzed: AnalyzedDocument
) -> ChunkingContext:
    """Assemble a :class:`ChunkingContext` from intelligence and parsed blocks."""
    breadcrumbs = _breadcrumbs(report.structure)
    section_flags = {section.section_id: section for section in report.sections}

    views: list[SectionView] = []
    preamble = [block for block in analyzed.blocks if block.section_id is None]
    if preamble:
        views.append(
            SectionView(
                section_id=None,
                title=_PREAMBLE_TITLE,
                level=0,
                breadcrumb=_PREAMBLE_TITLE,
                blocks=preamble,
                contains_table=_has(preamble, BlockType.TABLE),
                contains_code=_has(preamble, BlockType.CODE),
                contains_image=_has(preamble, BlockType.IMAGE),
            )
        )

    for node in report.structure:
        blocks = analyzed.blocks_for_section(node.section_id)
        flags = section_flags.get(node.section_id)
        views.append(
            SectionView(
                section_id=node.section_id,
                title=node.title,
                level=node.level,
                breadcrumb=breadcrumbs.get(node.section_id, node.title),
                blocks=blocks,
                contains_table=flags.contains_table if flags else _has(blocks, BlockType.TABLE),
                contains_code=flags.contains_code if flags else _has(blocks, BlockType.CODE),
                contains_image=flags.contains_image if flags else _has(blocks, BlockType.IMAGE),
            )
        )

    return ChunkingContext(
        document_id=report.document_id,
        markdown_version=report.document_version,
        language=report.language,
        classification=report.classification.value,
        quality_score=report.quality.overall,
        sections=views,
    )


def _has(blocks: list[MarkdownBlock], block_type: BlockType) -> bool:
    return any(block.block_type is block_type for block in blocks)

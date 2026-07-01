"""Section-tree construction shared by all analyzers (handbook 8.6)."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.intelligence.markdown_ast import MarkdownBlock, ParsedMarkdown
from domain.intelligence.models import BlockType, SectionNode

_TOKENS_PER_MINUTE = 200.0


def count_tokens(text: str) -> int:
    """Return an approximate whitespace token count for ``text``."""
    return len(text.split())


def reading_time_seconds(token_count: int) -> float:
    """Return an estimated reading time in seconds for ``token_count`` tokens."""
    return round(token_count / _TOKENS_PER_MINUTE * 60.0, 2)


@dataclass
class AnalyzedDocument:
    """A parsed document with its section tree resolved."""

    front_matter: dict[str, str]
    blocks: list[MarkdownBlock]
    sections: list[SectionNode] = field(default_factory=list)

    def blocks_for_section(self, section_id: str) -> list[MarkdownBlock]:
        """Return blocks directly assigned to ``section_id``."""
        return [block for block in self.blocks if block.section_id == section_id]


def build_analyzed_document(parsed: ParsedMarkdown) -> AnalyzedDocument:
    """Assign blocks to sections and build the logical section tree."""
    headings = [
        (position, block)
        for position, block in enumerate(parsed.blocks)
        if block.block_type is BlockType.HEADING
    ]

    children: dict[str, list[str]] = {}
    stack: list[tuple[int, str]] = []
    node_specs: list[tuple[str, str, int, str | None]] = []
    current_id: str | None = None

    counter = 0
    for _, block in headings:
        counter += 1
        section_id = f"SEC-{counter}"
        while stack and stack[-1][0] >= block.level:
            stack.pop()
        parent_id = stack[-1][1] if stack else None
        node_specs.append((section_id, block.text, block.level, parent_id))
        if parent_id is not None:
            children.setdefault(parent_id, []).append(section_id)
        stack.append((block.level, section_id))

    heading_iter = iter(node_specs)
    current_id = None
    for block in parsed.blocks:
        if block.block_type is BlockType.HEADING:
            current_id = next(heading_iter)[0]
            block.section_id = current_id
        else:
            block.section_id = current_id

    sections = [
        SectionNode(
            section_id=section_id,
            title=title,
            level=level,
            parent_id=parent_id,
            child_ids=children.get(section_id, []),
        )
        for section_id, title, level, parent_id in node_specs
    ]
    return AnalyzedDocument(
        front_matter=parsed.front_matter, blocks=parsed.blocks, sections=sections
    )

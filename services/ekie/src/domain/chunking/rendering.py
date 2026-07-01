"""Deterministic Markdown block rendering for chunk content (handbook 9.9-9.11)."""

from __future__ import annotations

from domain.intelligence import BlockType, MarkdownBlock


def render_block(block: MarkdownBlock) -> str:
    """Render a single parsed block back to canonical Markdown text."""
    if block.block_type is BlockType.HEADING:
        return f"{'#' * max(block.level, 1)} {block.text}".strip()
    if block.block_type is BlockType.CODE:
        fence = f"```{block.language}".rstrip()
        return f"{fence}\n{block.text}\n```"
    if block.block_type is BlockType.TABLE:
        return render_table(block.table_rows)
    if block.block_type is BlockType.IMAGE:
        return f"![{block.text}]({block.language})"
    if block.block_type in {BlockType.QUOTE, BlockType.NOTE}:
        return "\n".join(f"> {line}" for line in block.text.splitlines() or [""])
    return block.text


def render_table(rows: list[list[str]]) -> str:
    """Render table rows as a canonical Markdown table, preserving the header."""
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    header = _pad(rows[0], width)
    lines = [_render_row(header), _render_row(["---"] * width)]
    lines.extend(_render_row(_pad(row, width)) for row in rows[1:])
    return "\n".join(lines)


def _pad(row: list[str], width: int) -> list[str]:
    return list(row) + [""] * (width - len(row))


def _render_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"

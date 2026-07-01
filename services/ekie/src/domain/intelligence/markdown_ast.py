"""Line-based canonical Markdown parser producing a block AST (handbook 8.4).

The parser is deterministic and dependency-free. It recognizes the block types
emitted by the transformation framework: YAML front matter, headings, fenced
code, tables, blockquotes/notes, images, lists, and paragraphs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from domain.intelligence.models import BlockType

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
_IMAGE_ONLY = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]*)\)\s*$")
_LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+\.)\s+\S")
_NOTE_PREFIX = re.compile(r"^(note|warning|caution|important|tip)\b", re.IGNORECASE)


@dataclass
class MarkdownBlock:
    """A single structural block extracted from canonical Markdown."""

    block_type: BlockType
    text: str
    level: int = 0
    language: str = ""
    section_id: str | None = None
    table_rows: list[list[str]] = field(default_factory=list)


@dataclass
class ParsedMarkdown:
    """The parsed representation of a canonical Markdown document."""

    front_matter: dict[str, str] = field(default_factory=dict)
    blocks: list[MarkdownBlock] = field(default_factory=list)


def parse_markdown(text: str) -> ParsedMarkdown:
    """Parse canonical Markdown ``text`` into front matter and typed blocks."""
    lines = text.replace("\r\n", "\n").split("\n")
    index = 0
    front_matter: dict[str, str] = {}

    if lines and lines[0].strip() == "---":
        front_matter, index = _parse_front_matter(lines)

    blocks: list[MarkdownBlock] = []
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            block, index = _parse_code(lines, index)
            blocks.append(block)
            continue

        heading = _HEADING.match(stripped)
        if heading:
            blocks.append(
                MarkdownBlock(
                    block_type=BlockType.HEADING,
                    text=heading.group(2).strip(),
                    level=len(heading.group(1)),
                )
            )
            index += 1
            continue
        if _is_table_start(lines, index):
            block, index = _parse_table(lines, index)
            blocks.append(block)
            continue
        image = _IMAGE_ONLY.match(stripped)
        if image:
            blocks.append(
                MarkdownBlock(
                    block_type=BlockType.IMAGE,
                    text=image.group("alt"),
                    language=image.group("src"),
                )
            )
            index += 1
            continue
        if stripped.startswith(">"):
            block, index = _parse_quote(lines, index)
            blocks.append(block)
            continue
        if _LIST_ITEM.match(line):
            block, index = _parse_list(lines, index)
            blocks.append(block)
            continue

        block, index = _parse_paragraph(lines, index)
        blocks.append(block)

    return ParsedMarkdown(front_matter=front_matter, blocks=blocks)


def _parse_front_matter(lines: list[str]) -> tuple[dict[str, str], int]:
    front_matter: dict[str, str] = {}
    index = 1
    while index < len(lines) and lines[index].strip() != "---":
        raw = lines[index]
        if ":" in raw:
            key, _, value = raw.partition(":")
            front_matter[key.strip()] = _unquote(value.strip())
        index += 1
    return front_matter, index + 1


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def _parse_code(lines: list[str], index: int) -> tuple[MarkdownBlock, int]:
    language = lines[index].strip()[3:].strip()
    index += 1
    body: list[str] = []
    while index < len(lines) and not lines[index].strip().startswith("```"):
        body.append(lines[index])
        index += 1
    index += 1  # consume closing fence
    return (
        MarkdownBlock(
            block_type=BlockType.CODE, text="\n".join(body), language=language
        ),
        index,
    )


def _is_table_start(lines: list[str], index: int) -> bool:
    if "|" not in lines[index]:
        return False
    return index + 1 < len(lines) and bool(_TABLE_SEPARATOR.match(lines[index + 1]))


def _split_row(line: str) -> list[str]:
    trimmed = line.strip()
    if trimmed.startswith("|"):
        trimmed = trimmed[1:]
    if trimmed.endswith("|"):
        trimmed = trimmed[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", trimmed)]


def _parse_table(lines: list[str], index: int) -> tuple[MarkdownBlock, int]:
    rows: list[list[str]] = [_split_row(lines[index])]
    index += 2  # header + separator
    while index < len(lines) and lines[index].strip().startswith("|"):
        rows.append(_split_row(lines[index]))
        index += 1
    text = "\n".join(" ".join(row) for row in rows)
    return (
        MarkdownBlock(block_type=BlockType.TABLE, text=text, table_rows=rows),
        index,
    )


def _parse_quote(lines: list[str], index: int) -> tuple[MarkdownBlock, int]:
    body: list[str] = []
    while index < len(lines) and lines[index].strip().startswith(">"):
        body.append(lines[index].strip().lstrip(">").strip())
        index += 1
    text = "\n".join(body).strip()
    block_type = BlockType.NOTE if _NOTE_PREFIX.match(text) else BlockType.QUOTE
    return MarkdownBlock(block_type=block_type, text=text), index


def _parse_list(lines: list[str], index: int) -> tuple[MarkdownBlock, int]:
    body: list[str] = []
    while index < len(lines) and (
        _LIST_ITEM.match(lines[index]) or (lines[index].strip() and lines[index].startswith(" "))
    ):
        body.append(lines[index].rstrip())
        index += 1
    return MarkdownBlock(block_type=BlockType.LIST, text="\n".join(body)), index


def _parse_paragraph(lines: list[str], index: int) -> tuple[MarkdownBlock, int]:
    body: list[str] = []
    while index < len(lines):
        current = lines[index]
        stripped = current.strip()
        if not stripped or stripped.startswith(("#", "```", ">")):
            break
        if _LIST_ITEM.match(current) or _IMAGE_ONLY.match(stripped):
            break
        if _is_table_start(lines, index):
            break
        body.append(stripped)
        index += 1
    return MarkdownBlock(block_type=BlockType.PARAGRAPH, text=" ".join(body)), index

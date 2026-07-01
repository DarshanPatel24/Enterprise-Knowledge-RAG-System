"""CSV parser producing a canonical Markdown table (pure Python stdlib)."""

from __future__ import annotations

import csv
import io
from pathlib import PurePosixPath
from typing import ClassVar

from domain.transformation.parsers.base import (
    DocumentParser,
    ExtractedMetadata,
    ParsedContent,
    ParserContext,
    ParserError,
)


def _escape_cell(value: str) -> str:
    """Escape Markdown table delimiters within a cell value."""
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


class CsvParser(DocumentParser):
    """Parser converting CSV content into a Markdown table (handbook 7.11)."""

    parser_type: ClassVar[str] = "csv"
    parser_version: ClassVar[str] = "1.0"
    supported_extensions: ClassVar[frozenset[str]] = frozenset({"csv"})
    supported_mime_types: ClassVar[frozenset[str]] = frozenset({"text/csv"})

    def parse(self, data: bytes, context: ParserContext) -> ParsedContent:
        """Render CSV rows as a Markdown table with the first row as header."""
        text = self.decode(data)
        try:
            rows = [row for row in csv.reader(io.StringIO(text)) if row]
        except csv.Error as exc:  # pragma: no cover - malformed CSV is rare
            raise ParserError(f"failed to parse CSV: {exc}") from exc

        title = PurePosixPath(context.source_path).stem
        if not rows:
            return ParsedContent(body="", metadata=ExtractedMetadata(title=title))

        width = max(len(row) for row in rows)
        header = [_escape_cell(cell) for cell in rows[0]] + [""] * (width - len(rows[0]))
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(["---"] * width) + " |",
        ]
        for row in rows[1:]:
            cells = [_escape_cell(cell) for cell in row] + [""] * (width - len(row))
            lines.append("| " + " | ".join(cells) + " |")

        return ParsedContent(body="\n".join(lines), metadata=ExtractedMetadata(title=title))

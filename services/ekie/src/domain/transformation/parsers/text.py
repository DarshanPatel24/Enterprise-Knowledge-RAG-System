"""Plain text, source code, and Markdown parsers (pure Python)."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import ClassVar

from domain.transformation.parsers.base import (
    DocumentParser,
    ExtractedMetadata,
    ParsedContent,
    ParserContext,
)


def _stem_title(source_path: str) -> str:
    """Return a human title derived from the file name."""
    return PurePosixPath(source_path).stem


class PlainTextParser(DocumentParser):
    """Parser for plain-text documents (handbook 7.4 Documents)."""

    parser_type: ClassVar[str] = "plain_text"
    parser_version: ClassVar[str] = "1.0"
    supported_extensions: ClassVar[frozenset[str]] = frozenset({"txt", "text", "log", "rtf"})
    supported_mime_types: ClassVar[frozenset[str]] = frozenset({"text/plain"})

    def parse(self, data: bytes, context: ParserContext) -> ParsedContent:
        """Return the decoded text body with a filename-derived title."""
        text = self.decode(data)
        return ParsedContent(
            body=text,
            metadata=ExtractedMetadata(title=_stem_title(context.source_path)),
        )


class MarkdownParser(DocumentParser):
    """Pass-through parser for existing Markdown documents."""

    parser_type: ClassVar[str] = "markdown"
    parser_version: ClassVar[str] = "1.0"
    supported_extensions: ClassVar[frozenset[str]] = frozenset({"md", "markdown"})
    supported_mime_types: ClassVar[frozenset[str]] = frozenset({"text/markdown"})

    def parse(self, data: bytes, context: ParserContext) -> ParsedContent:
        """Return the Markdown body unchanged apart from decoding."""
        return ParsedContent(
            body=self.decode(data),
            metadata=ExtractedMetadata(title=_stem_title(context.source_path)),
        )

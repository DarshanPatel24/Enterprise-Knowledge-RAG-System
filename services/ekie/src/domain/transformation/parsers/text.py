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

_CODE_LANGUAGES: dict[str, str] = {
    "py": "python",
    "java": "java",
    "js": "javascript",
    "ts": "typescript",
    "json": "json",
    "xml": "xml",
    "yaml": "yaml",
    "yml": "yaml",
    "sql": "sql",
    "sh": "bash",
}


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


class SourceCodeParser(DocumentParser):
    """Parser wrapping source and structured-config files as fenced code."""

    parser_type: ClassVar[str] = "source_code"
    parser_version: ClassVar[str] = "1.0"
    supported_extensions: ClassVar[frozenset[str]] = frozenset(_CODE_LANGUAGES)
    supported_mime_types: ClassVar[frozenset[str]] = frozenset()

    def parse(self, data: bytes, context: ParserContext) -> ParsedContent:
        """Return the source wrapped in a language-annotated fenced code block."""
        language = _CODE_LANGUAGES.get(context.extension.lower(), "")
        code = self.decode(data).rstrip("\n")
        body = f"```{language}\n{code}\n```"
        return ParsedContent(
            body=body,
            metadata=ExtractedMetadata(title=_stem_title(context.source_path)),
        )

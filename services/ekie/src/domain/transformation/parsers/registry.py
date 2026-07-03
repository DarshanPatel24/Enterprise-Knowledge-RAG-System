"""Parser registry selecting a parser by extension or MIME type (handbook 7.6)."""

from __future__ import annotations

from domain.transformation.parsers.base import (
    DocumentParser,
    ParserContext,
    UnsupportedFormatError,
)
from domain.transformation.parsers.csv_parser import CsvParser
from domain.transformation.parsers.html import HtmlParser
from domain.transformation.parsers.rich_media import RichMediaParser
from domain.transformation.parsers.text import (
    MarkdownParser,
    PlainTextParser,
    SourceCodeParser,
)


class ParserRegistry:
    """Registry mapping document formats to their parsers."""

    def __init__(self) -> None:
        self._by_extension: dict[str, DocumentParser] = {}
        self._by_mime: dict[str, DocumentParser] = {}

    def register(self, parser: DocumentParser) -> None:
        """Register ``parser`` for each of its supported extensions and MIME types."""
        for extension in parser.supported_extensions:
            self._by_extension[extension.lower()] = parser
        for mime_type in parser.supported_mime_types:
            self._by_mime[mime_type.lower()] = parser

    def select(self, context: ParserContext) -> DocumentParser:
        """Return the parser for ``context`` by extension, then MIME type.

        Raises :class:`UnsupportedFormatError` when no parser is registered.
        """
        parser = self._by_extension.get(context.extension.lower())
        if parser is None and context.mime_type is not None:
            parser = self._by_mime.get(context.mime_type.lower())
        if parser is None:
            raise UnsupportedFormatError(
                f"no parser registered for extension {context.extension!r}"
            )
        return parser

    def registered_extensions(self) -> frozenset[str]:
        """Return the set of registered file extensions."""
        return frozenset(self._by_extension)


def default_registry() -> ParserRegistry:
    """Return a registry pre-populated with Phase 1 pure-Python parsers."""
    registry = ParserRegistry()
    for parser in (
        PlainTextParser(),
        MarkdownParser(),
        SourceCodeParser(),
        CsvParser(),
        HtmlParser(),
        RichMediaParser(),
    ):
        registry.register(parser)
    return registry

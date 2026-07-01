"""Parser subpackage for the Document Transformation Framework."""

from domain.transformation.parsers.base import (
    DocumentParser,
    ExtractedMetadata,
    ParsedContent,
    ParserContext,
    ParserError,
    UnsupportedFormatError,
)
from domain.transformation.parsers.csv_parser import CsvParser
from domain.transformation.parsers.html import HtmlParser
from domain.transformation.parsers.registry import ParserRegistry, default_registry
from domain.transformation.parsers.text import (
    MarkdownParser,
    PlainTextParser,
    SourceCodeParser,
)

__all__ = [
    "CsvParser",
    "DocumentParser",
    "ExtractedMetadata",
    "HtmlParser",
    "MarkdownParser",
    "ParsedContent",
    "ParserContext",
    "ParserError",
    "ParserRegistry",
    "PlainTextParser",
    "SourceCodeParser",
    "UnsupportedFormatError",
    "default_registry",
]

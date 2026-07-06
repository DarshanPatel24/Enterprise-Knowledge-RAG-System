"""Parser subpackage for the Document Transformation Framework."""

from domain.transformation.parsers.base import (
    DocumentParser,
    ExtractedMetadata,
    ParsedContent,
    ParserContext,
    ParserError,
    UnsupportedFormatError,
)
from domain.transformation.parsers.registry import ParserRegistry, default_registry
from domain.transformation.parsers.text import MarkdownParser, PlainTextParser

__all__ = [
    "DocumentParser",
    "ExtractedMetadata",
    "MarkdownParser",
    "ParsedContent",
    "ParserContext",
    "ParserError",
    "ParserRegistry",
    "PlainTextParser",
    "UnsupportedFormatError",
    "default_registry",
]

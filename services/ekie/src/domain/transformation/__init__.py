"""Document Transformation & Canonical Markdown Framework (EKIE handbook Chapter 7)."""

from domain.transformation.errors import TransformationError, TransformationErrorType
from domain.transformation.events import TransformationEvent, TransformationEventType
from domain.transformation.markdown_document import FrontMatter, MarkdownDocument
from domain.transformation.normalization import normalize_text
from domain.transformation.parsers import (
    DocumentParser,
    ExtractedMetadata,
    MarkdownParser,
    ParsedContent,
    ParserContext,
    ParserError,
    ParserRegistry,
    PlainTextParser,
    UnsupportedFormatError,
    default_registry,
)
from domain.transformation.pipeline import TransformationPipeline, TransformationResult
from domain.transformation.policy import TransformationPolicy
from domain.transformation.validation import (
    MarkdownValidator,
    ValidationError,
    ValidationReport,
)

__all__ = [
    "DocumentParser",
    "ExtractedMetadata",
    "FrontMatter",
    "MarkdownDocument",
    "MarkdownParser",
    "MarkdownValidator",
    "ParsedContent",
    "ParserContext",
    "ParserError",
    "ParserRegistry",
    "PlainTextParser",
    "TransformationError",
    "TransformationErrorType",
    "TransformationEvent",
    "TransformationEventType",
    "TransformationPipeline",
    "TransformationPolicy",
    "TransformationResult",
    "UnsupportedFormatError",
    "ValidationError",
    "ValidationReport",
    "default_registry",
    "normalize_text",
]

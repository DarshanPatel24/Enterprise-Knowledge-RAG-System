"""Parser abstraction for the Document Transformation Framework (handbook 7.6).

Parsers convert raw document bytes of a single format into an intermediate,
pre-normalization Markdown body plus extracted document metadata. They perform
no normalization, validation, or persistence; those are pipeline concerns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar


class ParserError(RuntimeError):
    """Raised when a parser cannot extract content from a document."""


class UnsupportedFormatError(LookupError):
    """Raised when no parser is registered for a document format."""


@dataclass(frozen=True)
class ParserContext:
    """Immutable context describing the document being parsed."""

    source_path: str
    extension: str
    mime_type: str | None = None


@dataclass(frozen=True)
class ExtractedMetadata:
    """Document metadata surfaced by a parser (handbook 7.9)."""

    title: str | None = None
    author: str | None = None
    language: str | None = None
    extra: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedContent:
    """Intermediate parser output prior to normalization."""

    body: str
    metadata: ExtractedMetadata = field(default_factory=ExtractedMetadata)


class DocumentParser(ABC):
    """Common interface every format parser implements (handbook ADR-012)."""

    parser_type: ClassVar[str]
    parser_version: ClassVar[str]
    supported_extensions: ClassVar[frozenset[str]]
    supported_mime_types: ClassVar[frozenset[str]] = frozenset()

    @abstractmethod
    def parse(self, data: bytes, context: ParserContext) -> ParsedContent:
        """Extract a Markdown body and metadata from ``data``.

        Implementations must raise :class:`ParserError` on unrecoverable
        extraction failures and must not mutate external state.
        """

    @staticmethod
    def decode(data: bytes) -> str:
        """Decode bytes as UTF-8, replacing invalid sequences deterministically."""
        return data.decode("utf-8", errors="replace")

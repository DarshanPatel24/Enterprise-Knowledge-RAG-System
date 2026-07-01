"""Chunking output contract, identity, and metadata models (handbook 9.15-9.16).

These models form the chunk contract consumed by the Embedding Framework
(Chapter 10). They are EKIE-internal and intentionally not part of
packages/contracts, which carries only cross-service payloads.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ChunkStrategy(StrEnum):
    """Chunking strategies supported by the framework (handbook 9.7)."""

    SEMANTIC = "semantic"
    SECTION_BASED = "section_based"
    HEADING_BASED = "heading_based"
    PARAGRAPH_BASED = "paragraph_based"
    TOKEN_BASED = "token_based"  # noqa: S105 - strategy label, not a credential
    TABLE_BASED = "table_based"
    CODE_BASED = "code_based"


class ChunkMetadata(BaseModel):
    """Rich metadata attached to every chunk asset (handbook 9.15)."""

    model_config = {"frozen": True}

    chunk_id: str
    document_id: str
    markdown_version: int
    section_id: str | None
    section_title: str
    breadcrumb: str
    heading_level: int
    chunk_sequence: int
    token_count: int
    language: str
    chunk_strategy: ChunkStrategy
    classification: str
    contains_table: bool
    contains_code: bool
    contains_image: bool
    quality_score: int


class Chunk(BaseModel):
    """A single knowledge chunk with content, hash, and metadata (handbook 9.15)."""

    model_config = {"frozen": True}

    content: str
    content_hash: str
    metadata: ChunkMetadata


class ChunkDocument(BaseModel):
    """The complete, versioned chunk set for a document (handbook 9.16, ADR-018)."""

    model_config = {"frozen": True}

    document_id: str
    markdown_version: int
    strategy: ChunkStrategy
    chunk_count: int
    total_tokens: int
    chunks: list[Chunk] = Field(default_factory=list)

    def canonical_json(self) -> bytes:
        """Return deterministic UTF-8 JSON bytes for immutable asset storage."""
        return self.model_dump_json(indent=2).encode("utf-8")

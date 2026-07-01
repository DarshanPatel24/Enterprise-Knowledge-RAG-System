"""Intelligent Chunking policy: configuration-driven boundaries (handbook 9.3, 9.14)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from domain.chunking.models import ChunkStrategy


class ChunkingSettingsLike(Protocol):
    """Structural type for environment-backed chunking settings."""

    default_strategy: str
    target_token_budget: int
    max_token_budget: int
    min_chunk_tokens: int
    preserve_tables: bool
    preserve_code: bool
    respect_section_boundaries: bool
    include_breadcrumb_context: bool


class ChunkingPolicy(BaseModel):
    """Versioned, configuration-driven chunking behavior (handbook 9.7, ADR-017)."""

    model_config = {"frozen": True}

    default_strategy: ChunkStrategy = ChunkStrategy.SEMANTIC
    target_token_budget: int = Field(default=512, gt=0)
    max_token_budget: int = Field(default=1024, gt=0)
    min_chunk_tokens: int = Field(default=8, ge=0)
    preserve_tables: bool = True
    preserve_code: bool = True
    respect_section_boundaries: bool = True
    include_breadcrumb_context: bool = True

    @classmethod
    def from_settings(cls, settings: ChunkingSettingsLike) -> ChunkingPolicy:
        """Build a policy from environment-backed chunking settings."""
        return cls(
            default_strategy=ChunkStrategy(settings.default_strategy),
            target_token_budget=settings.target_token_budget,
            max_token_budget=settings.max_token_budget,
            min_chunk_tokens=settings.min_chunk_tokens,
            preserve_tables=settings.preserve_tables,
            preserve_code=settings.preserve_code,
            respect_section_boundaries=settings.respect_section_boundaries,
            include_breadcrumb_context=settings.include_breadcrumb_context,
        )

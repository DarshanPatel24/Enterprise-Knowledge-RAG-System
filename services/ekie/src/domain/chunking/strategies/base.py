"""Chunk strategy plugin interface and draft type (handbook 9.7, ADR-015)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from domain.chunking.context import ChunkingContext
from domain.chunking.models import ChunkStrategy
from domain.chunking.policy import ChunkingPolicy


@dataclass(frozen=True)
class ChunkDraft:
    """A strategy's proposed chunk prior to identity and metadata assignment."""

    section_id: str | None
    section_title: str
    breadcrumb: str
    heading_level: int
    content: str
    token_count: int
    contains_table: bool
    contains_code: bool
    contains_image: bool


class ChunkStrategyPlugin(ABC):
    """A pluggable chunking strategy (handbook 9.7, ADR-015)."""

    strategy: ClassVar[ChunkStrategy]

    @abstractmethod
    def generate(
        self, context: ChunkingContext, policy: ChunkingPolicy
    ) -> list[ChunkDraft]:
        """Produce ordered chunk drafts for ``context`` under ``policy``."""

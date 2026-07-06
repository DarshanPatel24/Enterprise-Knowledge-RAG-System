"""Intelligent Chunking Framework (EKIE handbook Chapter 9)."""

from domain.chunking.context import (
    ChunkingContext,
    SectionView,
    build_context,
)
from domain.chunking.engine import ChunkingEngine, ChunkingResult
from domain.chunking.errors import ChunkingError, ChunkingErrorType
from domain.chunking.events import ChunkingEvent, ChunkingEventType
from domain.chunking.models import (
    Chunk,
    ChunkDocument,
    ChunkMetadata,
    ChunkStrategy,
)
from domain.chunking.policy import ChunkingPolicy
from domain.chunking.rendering import render_block, render_table
from domain.chunking.strategies import (
    ChunkDraft,
    ChunkStrategyPlugin,
    ChunkStrategyRegistry,
    RecursiveCharacterChunkStrategy,
    SemanticChunkStrategy,
    TokenWindowChunkStrategy,
    default_registry,
)
from domain.chunking.tokens import estimate_tokens
from domain.chunking.validation import (
    ChunkValidationErrorType,
    ChunkValidationReport,
    ChunkValidator,
)

__all__ = [
    "Chunk",
    "ChunkDocument",
    "ChunkDraft",
    "ChunkMetadata",
    "ChunkStrategy",
    "ChunkStrategyPlugin",
    "ChunkStrategyRegistry",
    "ChunkValidationErrorType",
    "ChunkValidationReport",
    "ChunkValidator",
    "ChunkingContext",
    "ChunkingEngine",
    "ChunkingError",
    "ChunkingErrorType",
    "ChunkingEvent",
    "ChunkingEventType",
    "ChunkingPolicy",
    "ChunkingResult",
    "RecursiveCharacterChunkStrategy",
    "SectionView",
    "SemanticChunkStrategy",
    "TokenWindowChunkStrategy",
    "build_context",
    "default_registry",
    "estimate_tokens",
    "render_block",
    "render_table",
]

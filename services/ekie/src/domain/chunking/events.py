"""Standardized chunking events (handbook 9.6).

EKIE-internal signals emitted by the chunking engine. Not part of
packages/contracts, which carries only cross-service payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChunkingEventType(StrEnum):
    """Lifecycle events produced while chunking a document."""

    CHUNKING_STARTED = "ChunkingStarted"
    CHUNKS_GENERATED = "ChunksGenerated"
    CHUNKS_VALIDATED = "ChunksValidated"
    ASSET_STORED = "AssetStored"
    CHUNKING_SKIPPED = "ChunkingSkipped"
    CHUNKING_FAILED = "ChunkingFailed"


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class ChunkingEvent(BaseModel):
    """An immutable record of a chunking lifecycle occurrence."""

    model_config = {"frozen": True}

    event_type: ChunkingEventType
    document_id: str
    tenant_id: str
    asset_id: str | None = None
    version: int | None = None
    detail: str = ""
    timestamp: datetime = Field(default_factory=_utc_now)

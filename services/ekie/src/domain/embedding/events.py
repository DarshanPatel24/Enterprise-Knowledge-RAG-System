"""Standardized embedding events (handbook 10.8).

EKIE-internal signals emitted by the embedding engine. Not part of
packages/contracts, which carries only cross-service payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EmbeddingEventType(StrEnum):
    """Lifecycle events produced while embedding a document."""

    EMBEDDING_STARTED = "EmbeddingStarted"
    MODEL_SELECTED = "ModelSelected"
    EMBEDDINGS_GENERATED = "EmbeddingsGenerated"
    EMBEDDINGS_VALIDATED = "EmbeddingsValidated"
    ASSET_STORED = "AssetStored"
    EMBEDDING_SKIPPED = "EmbeddingSkipped"
    EMBEDDING_FAILED = "EmbeddingFailed"


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class EmbeddingEvent(BaseModel):
    """An immutable record of an embedding lifecycle occurrence."""

    model_config = {"frozen": True}

    event_type: EmbeddingEventType
    document_id: str
    tenant_id: str
    asset_id: str | None = None
    version: int | None = None
    detail: str = ""
    timestamp: datetime = Field(default_factory=_utc_now)

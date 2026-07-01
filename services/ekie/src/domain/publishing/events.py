"""Standardized vector publishing events (handbook 11.6).

EKIE-internal signals emitted by the publishing engine. Not part of
packages/contracts, which carries only cross-service payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PublishEventType(StrEnum):
    """Lifecycle events produced while publishing a document's vectors."""

    PUBLISH_STARTED = "PublishStarted"
    COLLECTION_READY = "CollectionReady"
    VECTORS_PUBLISHED = "VectorsPublished"
    VECTORS_VERIFIED = "VectorsVerified"
    ASSET_STORED = "AssetStored"
    PUBLISH_SKIPPED = "PublishSkipped"
    PUBLISH_FAILED = "PublishFailed"


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class PublishEvent(BaseModel):
    """An immutable record of a publishing lifecycle occurrence."""

    model_config = {"frozen": True}

    event_type: PublishEventType
    document_id: str
    tenant_id: str
    collection: str = ""
    asset_id: str | None = None
    version: int | None = None
    detail: str = ""
    timestamp: datetime = Field(default_factory=_utc_now)

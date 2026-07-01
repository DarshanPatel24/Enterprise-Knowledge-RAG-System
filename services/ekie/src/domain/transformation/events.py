"""Standardized transformation events (handbook 7.7).

These events are EKIE-internal signals emitted by the transformation pipeline.
They are intentionally not part of packages/contracts, which carries only
cross-service payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TransformationEventType(StrEnum):
    """Lifecycle events produced while transforming a document."""

    TRANSFORMATION_STARTED = "TransformationStarted"
    MARKDOWN_GENERATED = "MarkdownGenerated"
    TRANSFORMATION_VALIDATED = "TransformationValidated"
    ASSET_STORED = "AssetStored"
    TRANSFORMATION_SKIPPED = "TransformationSkipped"
    TRANSFORMATION_FAILED = "TransformationFailed"


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class TransformationEvent(BaseModel):
    """An immutable record of a transformation lifecycle occurrence."""

    model_config = {"frozen": True}

    event_type: TransformationEventType
    document_id: str
    tenant_id: str
    asset_id: str | None = None
    version: int | None = None
    detail: str = ""
    timestamp: datetime = Field(default_factory=_utc_now)

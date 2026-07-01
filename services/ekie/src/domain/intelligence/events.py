"""Standardized document intelligence events (handbook 8.16).

EKIE-internal signals emitted by the intelligence engine. Not part of
packages/contracts, which carries only cross-service payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class IntelligenceEventType(StrEnum):
    """Lifecycle events produced while enriching a document."""

    INTELLIGENCE_STARTED = "IntelligenceStarted"
    REPORT_GENERATED = "ReportGenerated"
    ASSET_STORED = "AssetStored"
    INTELLIGENCE_SKIPPED = "IntelligenceSkipped"
    INTELLIGENCE_FAILED = "IntelligenceFailed"


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class IntelligenceEvent(BaseModel):
    """An immutable record of an intelligence lifecycle occurrence."""

    model_config = {"frozen": True}

    event_type: IntelligenceEventType
    document_id: str
    tenant_id: str
    asset_id: str | None = None
    version: int | None = None
    detail: str = ""
    timestamp: datetime = Field(default_factory=_utc_now)

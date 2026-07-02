"""Standardized orchestration events (handbook 6.20).

EKIE-internal signals emitted while orchestrating an ingestion workflow. Not
part of packages/contracts, which carries only cross-service payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field

from domain.orchestration.state import StageName


class OrchestrationEventType(StrEnum):
    """Lifecycle events produced while orchestrating an ingestion workflow."""

    WORKFLOW_STARTED = "WorkflowStarted"
    STAGE_STARTED = "StageStarted"
    STAGE_SKIPPED = "StageSkipped"
    STAGE_RETRIED = "StageRetried"
    STAGE_COMPLETED = "StageCompleted"
    STAGE_FAILED = "StageFailed"
    WORKFLOW_COMPLETED = "WorkflowCompleted"
    WORKFLOW_DEAD_LETTERED = "WorkflowDeadLettered"


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class OrchestrationEvent(BaseModel):
    """An immutable record of an orchestration lifecycle occurrence."""

    model_config = {"frozen": True}

    event_type: OrchestrationEventType
    document_id: str
    tenant_id: str
    correlation_id: str
    stage: StageName | None = None
    detail: str = ""
    timestamp: datetime = Field(default_factory=_utc_now)


class EventSink(Protocol):
    """Callable that receives orchestration events as the workflow progresses."""

    def __call__(
        self,
        event_type: OrchestrationEventType,
        stage: StageName | None = None,
        detail: str = "",
    ) -> None:
        """Record an orchestration event."""
        ...

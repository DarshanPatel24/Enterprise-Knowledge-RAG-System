"""Platform event bus (handbook Chapter 15).

The broader enterprise event platform: a standard event schema and an append-only
bus that carries workflow, knowledge, and approval events across the platform.
The in-memory bus is deterministic for tests; the logging bus emits structured
records. Durable streaming is a later concern.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from domain.observability import get_correlation_id, get_logger

logger = get_logger("ekcp.workflow.events")


class PlatformEventType(StrEnum):
    """Platform event types spanning workflow and knowledge (handbook 15, 16)."""

    WORKFLOW_TRIGGERED = "workflow_triggered"
    WORKFLOW_PLANNED = "workflow_planned"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_REPLANNED = "workflow_replanned"
    WORKFLOW_MILESTONE_REACHED = "workflow_milestone_reached"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RECEIVED = "approval_received"
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    KNOWLEDGE_RETRIEVAL_FAILED = "knowledge_retrieval_failed"
    CONTEXT_DEGRADED = "context_degraded"


class PlatformEvent(BaseModel):
    """Immutable standard platform event (handbook 15)."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    event_type: PlatformEventType
    tenant_id: str
    source_service: str = "ekcp"
    correlation_id: str | None = None
    payload: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventBus(ABC):
    """Append-only platform event bus."""

    @abstractmethod
    def publish(self, event: PlatformEvent) -> None:
        """Publish a platform event."""


class InMemoryEventBus(EventBus):
    """Append-only in-memory event bus (deterministic for tests)."""

    def __init__(self) -> None:
        self._events: list[PlatformEvent] = []

    def publish(self, event: PlatformEvent) -> None:
        self._events.append(event)

    def history(self, *, tenant_id: str | None = None) -> tuple[PlatformEvent, ...]:
        """Return an immutable snapshot of published events, optionally by tenant."""
        if tenant_id is None:
            return tuple(self._events)
        return tuple(e for e in self._events if e.tenant_id == tenant_id)


class LoggingEventBus(EventBus):
    """Event bus that emits one structured log record per event."""

    def publish(self, event: PlatformEvent) -> None:
        logger.info(
            "platform_event",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "tenant_id": event.tenant_id,
                "source_service": event.source_service,
            },
        )


def build_platform_event(
    event_type: PlatformEventType,
    *,
    tenant_id: str,
    source_service: str = "ekcp",
    payload: dict[str, str] | None = None,
) -> PlatformEvent:
    """Build a platform event with the current correlation id bound."""
    return PlatformEvent(
        event_type=event_type,
        tenant_id=tenant_id,
        source_service=source_service,
        correlation_id=get_correlation_id(),
        payload=payload or {},
    )

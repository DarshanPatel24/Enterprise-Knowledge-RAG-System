"""Conversation event dispatch.

Events are the coordination substrate: every significant lifecycle and
interaction moment is published to a sink. The in-memory sink is append-only and
deterministic for tests; a logging sink emits structured records. Later sprints
add durable event streams behind the same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from domain.observability import get_correlation_id, get_logger

logger = get_logger("ekcp.conversation.events")


class ConversationEventType(StrEnum):
    """Conversation event types (handbook Chapter 4 Event Dispatcher)."""

    CONVERSATION_CREATED = "conversation_created"
    INTERACTION_STARTED = "interaction_started"
    CONTEXT_READY = "context_ready"
    AGENT_INVOKED = "agent_invoked"
    AGENT_COMPLETED = "agent_completed"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    RESPONSE_GENERATED = "response_generated"
    MEMORY_UPDATED = "memory_updated"
    CLARIFICATION_REQUESTED = "clarification_requested"
    CONVERSATION_COMPLETED = "conversation_completed"
    CONVERSATION_ARCHIVED = "conversation_archived"
    CONVERSATION_PAUSED = "conversation_paused"
    CONVERSATION_RESUMED = "conversation_resumed"


class ConversationEvent(BaseModel):
    """Immutable conversation event."""

    model_config = ConfigDict(frozen=True)

    event_type: ConversationEventType
    conversation_id: str
    tenant_id: str
    correlation_id: str | None = None
    detail: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventSink(ABC):
    """Abstract conversation event sink."""

    @abstractmethod
    def publish(self, event: ConversationEvent) -> None:
        """Publish a conversation event."""


class InMemoryEventSink(EventSink):
    """Append-only in-memory event sink (deterministic for tests)."""

    def __init__(self) -> None:
        self._events: list[ConversationEvent] = []

    def publish(self, event: ConversationEvent) -> None:
        self._events.append(event)

    def history(self) -> tuple[ConversationEvent, ...]:
        """Return the append-only event history."""
        return tuple(self._events)


class LoggingEventSink(EventSink):
    """Event sink that emits one structured log record per event."""

    def publish(self, event: ConversationEvent) -> None:
        logger.info(
            "conversation_event",
            extra={
                "event_type": event.event_type,
                "conversation_id": event.conversation_id,
                "tenant_id": event.tenant_id,
            },
        )


def build_event(
    event_type: ConversationEventType,
    *,
    conversation_id: str,
    tenant_id: str,
    detail: dict[str, str] | None = None,
) -> ConversationEvent:
    """Build a conversation event with the current correlation id bound."""
    return ConversationEvent(
        event_type=event_type,
        conversation_id=conversation_id,
        tenant_id=tenant_id,
        correlation_id=get_correlation_id(),
        detail=detail or {},
    )

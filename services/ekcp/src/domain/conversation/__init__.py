"""Conversation core domain: lifecycle, CDT, store, events, engine."""

from domain.conversation.engine import ConversationEngine, InteractionResult
from domain.conversation.errors import ConversationError, ConversationErrorType
from domain.conversation.events import (
    ConversationEvent,
    ConversationEventType,
    EventSink,
    InMemoryEventSink,
    LoggingEventSink,
    build_event,
)
from domain.conversation.lifecycle import ensure_transition, is_allowed, transition
from domain.conversation.manager import ConversationManager
from domain.conversation.models import (
    ConversationDigitalTwin,
    ConversationMetrics,
    ConversationState,
    Interaction,
    InteractionStatus,
    InteractionType,
    MessageRole,
    OwnershipModel,
    StateTransition,
)
from domain.conversation.policy import ConversationPolicy, ConversationSettingsLike
from domain.conversation.store import ConversationStore, InMemoryConversationStore

__all__ = [
    "ConversationDigitalTwin",
    "ConversationEngine",
    "ConversationError",
    "ConversationErrorType",
    "ConversationEvent",
    "ConversationEventType",
    "ConversationManager",
    "ConversationMetrics",
    "ConversationPolicy",
    "ConversationSettingsLike",
    "ConversationState",
    "ConversationStore",
    "EventSink",
    "InMemoryConversationStore",
    "InMemoryEventSink",
    "Interaction",
    "InteractionResult",
    "InteractionStatus",
    "InteractionType",
    "LoggingEventSink",
    "MessageRole",
    "OwnershipModel",
    "StateTransition",
    "build_event",
    "ensure_transition",
    "is_allowed",
    "transition",
]

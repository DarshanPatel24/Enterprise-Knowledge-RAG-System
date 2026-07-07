"""Composition root: build EKCP foundations from settings.

Wires the settings module into engine-owned domain objects (config over code).
Domain packages stay independent of the settings module; this root is the single
place that reads settings and injects dependencies. The root grows one builder
at a time as the sprint track advances.
"""

from __future__ import annotations

from config.settings import EkcpSettings
from domain.context import (
    ContextAssembler,
    ContextPolicy,
    ContextStore,
    InMemoryContextStore,
)
from domain.conversation import (
    ConversationEngine,
    ConversationManager,
    ConversationPolicy,
    EventSink,
    InMemoryConversationStore,
    InMemoryEventSink,
    LoggingEventSink,
)
from domain.intent import IntentClassifier, IntentGate, IntentPolicy
from domain.observability import build_langfuse_callbacks, configure_logging
from domain.prompt import (
    PromptOrchestrator,
    PromptPolicy,
    default_prompt_registry,
)
from domain.security import SecurityContextValidator
from domain.session import InMemorySessionStore, SessionManager

__all__ = [
    "build_context_assembler",
    "build_context_store",
    "build_conversation_engine",
    "build_conversation_manager",
    "build_conversation_store",
    "build_event_sink",
    "build_intent_gate",
    "build_prompt_orchestrator",
    "build_security_validator",
    "build_session_manager",
    "build_session_store",
    "build_tracing_callbacks",
    "configure_observability",
]


def configure_observability(settings: EkcpSettings) -> None:
    """Install structured JSON logging from the observability settings."""
    configure_logging(
        service_name=settings.observability.service_name,
        log_level=settings.observability.log_level,
    )


def build_security_validator(settings: EkcpSettings) -> SecurityContextValidator:
    """Build the security context ingress validator from settings."""
    return SecurityContextValidator.from_settings(settings.security)


def build_tracing_callbacks(settings: EkcpSettings) -> list[object]:
    """Build Langfuse tracing callbacks from settings (empty when disabled)."""
    return list(build_langfuse_callbacks(settings.observability))


def build_conversation_store(settings: EkcpSettings) -> InMemoryConversationStore:
    """Build the conversation store (in-memory offline default)."""
    _ = settings.control_plane  # driver=mssql wires the SQL Server store in a later sprint
    return InMemoryConversationStore()


def build_event_sink(settings: EkcpSettings) -> EventSink:
    """Build the conversation event sink from settings."""
    if settings.conversation.event_sink == "logging":
        return LoggingEventSink()
    return InMemoryEventSink()


def build_conversation_manager(
    settings: EkcpSettings,
    store: InMemoryConversationStore,
    *,
    event_sink: EventSink | None = None,
) -> ConversationManager:
    """Build the conversation administration manager from settings."""
    policy = ConversationPolicy.from_settings(settings.conversation)
    return ConversationManager(store, policy=policy, event_sink=event_sink)


def build_session_store(settings: EkcpSettings) -> InMemorySessionStore:
    """Build the session store (in-memory offline default)."""
    _ = settings.redis  # enabled=True wires the Redis session store in a later sprint
    return InMemorySessionStore()


def build_session_manager(
    settings: EkcpSettings, store: InMemorySessionStore
) -> SessionManager:
    """Build the session manager from settings."""
    return SessionManager(
        store, session_ttl_seconds=settings.session.session_ttl_seconds
    )


def build_intent_gate(settings: EkcpSettings) -> IntentGate:
    """Build the intent-before-execution gate from settings."""
    policy = IntentPolicy.from_settings(settings.intent)
    return IntentGate(IntentClassifier(policy))


def build_conversation_engine(
    settings: EkcpSettings,
    store: InMemoryConversationStore,
    *,
    intent_gate: IntentGate | None = None,
    event_sink: EventSink | None = None,
) -> ConversationEngine:
    """Build the conversation engine (core interaction loop) from settings."""
    return ConversationEngine(
        store=store,
        intent_gate=intent_gate or build_intent_gate(settings),
        event_sink=event_sink,
        enable_events=settings.conversation.enable_events,
    )


def build_context_store(settings: EkcpSettings) -> ContextStore:
    """Build the context package store (in-memory offline default)."""
    _ = settings.redis  # enabled=True wires a cache-backed store in a later sprint
    return InMemoryContextStore()


def build_context_assembler(settings: EkcpSettings) -> ContextAssembler:
    """Build the context assembler from settings."""
    return ContextAssembler(ContextPolicy.from_settings(settings.context))


def build_prompt_orchestrator(settings: EkcpSettings) -> PromptOrchestrator:
    """Build the prompt orchestrator from settings and the template registry."""
    return PromptOrchestrator(
        PromptPolicy.from_settings(settings.prompt),
        registry=default_prompt_registry(),
    )

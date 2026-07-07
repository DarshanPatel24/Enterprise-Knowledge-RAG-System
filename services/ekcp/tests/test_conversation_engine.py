"""Tests for the conversation engine core interaction loop."""

from __future__ import annotations

import pytest

from config.settings import EkcpSettings
from domain.conversation import (
    ConversationEngine,
    ConversationError,
    ConversationErrorType,
    ConversationManager,
    ConversationPolicy,
    ConversationState,
    InMemoryConversationStore,
    InMemoryEventSink,
    InteractionStatus,
)
from domain.intent import IntentClassifier, IntentGate, IntentPolicy


def _harness() -> tuple[ConversationManager, ConversationEngine, InMemoryEventSink]:
    settings = EkcpSettings(_env_file=None)
    store = InMemoryConversationStore()
    sink = InMemoryEventSink()
    manager = ConversationManager(
        store,
        policy=ConversationPolicy.from_settings(settings.conversation),
        event_sink=sink,
    )
    gate = IntentGate(IntentClassifier(IntentPolicy.from_settings(settings.intent)))
    engine = ConversationEngine(store=store, intent_gate=gate, event_sink=sink)
    return manager, engine, sink


def _start(manager: ConversationManager) -> str:
    cdt = manager.create(tenant_id="tenant-a", owner_id="analyst-1", title="t")
    return cdt.conversation_id


def test_first_interaction_activates_and_records() -> None:
    manager, engine, sink = _harness()
    conversation_id = _start(manager)

    result = engine.handle_interaction(
        "tenant-a", conversation_id, message="What is the company policy on leave?"
    )

    assert result.conversation.current_state is ConversationState.ACTIVE
    assert result.conversation.metrics.interaction_count == 1
    assert result.interaction.status is InteractionStatus.COMPLETED
    assert result.decision.allow_execution is True
    event_types = [event.event_type for event in sink.history()]
    assert "conversation_created" in event_types
    assert "interaction_started" in event_types
    assert "response_generated" in event_types


def test_ambiguous_interaction_requests_clarification_and_waits() -> None:
    manager, engine, _ = _harness()
    conversation_id = _start(manager)

    result = engine.handle_interaction("tenant-a", conversation_id, message="hmm")

    assert result.conversation.current_state is ConversationState.WAITING
    assert result.interaction.status is InteractionStatus.WAITING
    assert result.interaction.assistant_response
    assert result.conversation.metrics.human_intervention_count == 1


def test_waiting_then_answer_reactivates() -> None:
    manager, engine, _ = _harness()
    conversation_id = _start(manager)
    engine.handle_interaction("tenant-a", conversation_id, message="hmm")

    result = engine.handle_interaction(
        "tenant-a", conversation_id, message="What is the company remote work policy?"
    )
    assert result.conversation.current_state is ConversationState.ACTIVE
    assert result.conversation.metrics.interaction_count == 2


def test_empty_message_rejected() -> None:
    manager, engine, _ = _harness()
    conversation_id = _start(manager)
    with pytest.raises(ConversationError) as exc:
        engine.handle_interaction("tenant-a", conversation_id, message="   ")
    assert exc.value.error_type == ConversationErrorType.EMPTY_MESSAGE


def test_completed_conversation_rejects_interaction() -> None:
    manager, engine, _ = _harness()
    conversation_id = _start(manager)
    engine.handle_interaction("tenant-a", conversation_id, message="hello there world")
    manager.complete("tenant-a", conversation_id)
    with pytest.raises(ConversationError) as exc:
        engine.handle_interaction("tenant-a", conversation_id, message="another message")
    assert exc.value.error_type == ConversationErrorType.INVALID_STATE

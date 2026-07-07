"""Tests for the conversation lifecycle state machine and store."""

from __future__ import annotations

import pytest

from domain.conversation import (
    ConversationDigitalTwin,
    ConversationError,
    ConversationErrorType,
    ConversationState,
    InMemoryConversationStore,
    is_allowed,
    transition,
)


def _cdt(state: ConversationState = ConversationState.CREATED) -> ConversationDigitalTwin:
    return ConversationDigitalTwin(
        conversation_id="conv-1",
        workspace_id="default",
        tenant_id="tenant-a",
        title="t",
        owner_id="analyst-1",
        current_state=state,
    )


def test_legal_transition_matrix() -> None:
    assert is_allowed(ConversationState.CREATED, ConversationState.ACTIVE)
    assert is_allowed(ConversationState.ACTIVE, ConversationState.WAITING)
    assert is_allowed(ConversationState.COMPLETED, ConversationState.ARCHIVED)
    assert not is_allowed(ConversationState.ARCHIVED, ConversationState.WAITING)
    assert not is_allowed(ConversationState.ACTIVE, ConversationState.CREATED)


def test_transition_records_history_and_bumps_version() -> None:
    cdt = _cdt()
    active = transition(cdt, ConversationState.ACTIVE, reason="first interaction")
    assert active.current_state is ConversationState.ACTIVE
    assert active.version_number == cdt.version_number + 1
    assert active.state_transition_history[-1].to_state is ConversationState.ACTIVE
    assert active.state_transition_history[-1].reason == "first interaction"


def test_illegal_transition_raises() -> None:
    with pytest.raises(ConversationError) as exc:
        transition(_cdt(ConversationState.ARCHIVED), ConversationState.WAITING, reason="x")
    assert exc.value.error_type == ConversationErrorType.INVALID_TRANSITION


def test_store_create_and_get() -> None:
    store = InMemoryConversationStore()
    cdt = _cdt()
    store.save(cdt, expected_version=None)
    loaded = store.get("tenant-a", "conv-1")
    assert loaded.conversation_id == "conv-1"


def test_store_not_found() -> None:
    with pytest.raises(ConversationError) as exc:
        InMemoryConversationStore().get("tenant-a", "missing")
    assert exc.value.error_type == ConversationErrorType.NOT_FOUND


def test_store_version_conflict() -> None:
    store = InMemoryConversationStore()
    cdt = _cdt()
    store.save(cdt, expected_version=None)
    # Save an update with the correct expected version, then a stale one.
    updated = cdt.model_copy(update={"version_number": 1})
    store.save(updated, expected_version=0)
    with pytest.raises(ConversationError) as exc:
        store.save(cdt.model_copy(update={"version_number": 2}), expected_version=0)
    assert exc.value.error_type == ConversationErrorType.VERSION_CONFLICT

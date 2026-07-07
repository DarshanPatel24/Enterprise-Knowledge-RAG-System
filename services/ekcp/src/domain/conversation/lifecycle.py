"""Conversation lifecycle state machine.

Encodes the handbook's legal state transitions and applies a validated
transition to an immutable :class:`ConversationDigitalTwin`, appending the change
to the transition history and bumping the version. Illegal transitions raise a
:class:`ConversationError`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.conversation.errors import ConversationError, ConversationErrorType
from domain.conversation.models import (
    ConversationDigitalTwin,
    ConversationState,
    StateTransition,
)

# Legal transitions per handbook Chapter 4. RECOVERING -> FAILED is represented
# as RECOVERING -> COMPLETED/ACTIVE here; a hard failure is surfaced as an error.
_ALLOWED_TRANSITIONS: dict[ConversationState, frozenset[ConversationState]] = {
    ConversationState.CREATED: frozenset({ConversationState.ACTIVE}),
    ConversationState.ACTIVE: frozenset(
        {
            ConversationState.WAITING,
            ConversationState.PAUSED,
            ConversationState.COMPLETED,
            ConversationState.RECOVERING,
        }
    ),
    ConversationState.WAITING: frozenset(
        {
            ConversationState.ACTIVE,
            ConversationState.COMPLETED,
            ConversationState.RECOVERING,
        }
    ),
    ConversationState.PAUSED: frozenset(
        {ConversationState.ACTIVE, ConversationState.COMPLETED}
    ),
    ConversationState.COMPLETED: frozenset(
        {ConversationState.ARCHIVED, ConversationState.ACTIVE}
    ),
    ConversationState.ARCHIVED: frozenset({ConversationState.ACTIVE}),
    ConversationState.RECOVERING: frozenset(
        {ConversationState.ACTIVE, ConversationState.COMPLETED}
    ),
}


def is_allowed(from_state: ConversationState, to_state: ConversationState) -> bool:
    """Return whether ``from_state`` may legally transition to ``to_state``."""
    return to_state in _ALLOWED_TRANSITIONS.get(from_state, frozenset())


def ensure_transition(from_state: ConversationState, to_state: ConversationState) -> None:
    """Raise :class:`ConversationError` when the transition is not permitted."""
    if not is_allowed(from_state, to_state):
        raise ConversationError(
            ConversationErrorType.INVALID_TRANSITION,
            f"illegal transition {from_state} -> {to_state}",
        )


def transition(
    cdt: ConversationDigitalTwin,
    to_state: ConversationState,
    *,
    reason: str,
    now: datetime | None = None,
) -> ConversationDigitalTwin:
    """Return a new CDT transitioned to ``to_state`` with history and version bump."""
    ensure_transition(cdt.current_state, to_state)
    timestamp = now or datetime.now(UTC)
    record = StateTransition(
        from_state=cdt.current_state,
        to_state=to_state,
        reason=reason,
        timestamp=timestamp,
    )
    return cdt.model_copy(
        update={
            "current_state": to_state,
            "state_transition_history": (*cdt.state_transition_history, record),
            "version_number": cdt.version_number + 1,
            "last_modified": timestamp,
        }
    )

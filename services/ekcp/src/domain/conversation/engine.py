"""Conversation Engine: the governed core interaction loop.

Implements the S1 subset of the canonical execution cycle: receive an
interaction, validate conversation state, load the Conversation Digital Twin,
gate intent before execution, record the interaction, update and persist the CDT
with optimistic concurrency, and dispatch events. Context assembly, generation,
agents, and tools land in later sprints; this engine guarantees that execution
never proceeds from raw, ungated user input.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

from domain.conversation.errors import ConversationError, ConversationErrorType
from domain.conversation.events import (
    ConversationEventType,
    EventSink,
    build_event,
)
from domain.conversation.lifecycle import transition
from domain.conversation.models import (
    ConversationDigitalTwin,
    ConversationState,
    Interaction,
    InteractionStatus,
    InteractionType,
)
from domain.conversation.store import ConversationStore
from domain.intent import IntentDecision, IntentGate, IntentType
from domain.observability import get_logger

logger = get_logger("ekcp.conversation.engine")

# Non-interactive states reject new interactions until an admin action resumes.
_NON_INTERACTIVE = frozenset(
    {
        ConversationState.PAUSED,
        ConversationState.COMPLETED,
        ConversationState.ARCHIVED,
        ConversationState.RECOVERING,
    }
)

_INTENT_TO_INTERACTION = {
    IntentType.QUESTION: InteractionType.QUERY,
    IntentType.TASK: InteractionType.TASK,
    IntentType.WORKFLOW: InteractionType.WORKFLOW,
    IntentType.ANALYSIS: InteractionType.ANALYSIS,
    IntentType.COLLABORATION: InteractionType.COLLABORATION,
    IntentType.AGENT_REQUEST: InteractionType.AGENT_REQUEST,
}


class InteractionResult(BaseModel):
    """Immutable result of handling one interaction."""

    model_config = ConfigDict(frozen=True)

    conversation: ConversationDigitalTwin
    interaction: Interaction
    decision: IntentDecision


class ConversationEngine:
    """Handle interactions against a persisted Conversation Digital Twin."""

    def __init__(
        self,
        *,
        store: ConversationStore,
        intent_gate: IntentGate,
        event_sink: EventSink | None = None,
        enable_events: bool = True,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._gate = intent_gate
        self._event_sink = event_sink
        self._enable_events = enable_events
        self._clock = clock or (lambda: datetime.now(UTC))

    def handle_interaction(
        self, tenant_id: str, conversation_id: str, *, message: str
    ) -> InteractionResult:
        """Run the governed interaction loop and return the interaction result."""
        text = message.strip()
        if not text:
            raise ConversationError(
                ConversationErrorType.EMPTY_MESSAGE, "message must not be empty"
            )

        cdt = self._store.get(tenant_id, conversation_id)
        expected_version = cdt.version_number

        if cdt.current_state in _NON_INTERACTIVE:
            raise ConversationError(
                ConversationErrorType.INVALID_STATE,
                f"conversation is {cdt.current_state} and cannot accept interactions",
            )

        # Step: activate the conversation (CREATED/WAITING -> ACTIVE).
        working = self._activate(cdt)
        self._emit(ConversationEventType.INTERACTION_STARTED, working)

        # Step: intent before execution.
        decision = self._gate.evaluate(text)
        classification = decision.classification

        # Step: record the interaction.
        clarifying = classification.requires_clarification
        interaction = Interaction(
            interaction_id=f"int-{uuid.uuid4().hex[:12]}",
            interaction_type=_INTENT_TO_INTERACTION[classification.intent],
            status=InteractionStatus.WAITING if clarifying else InteractionStatus.COMPLETED,
            user_message=text,
            assistant_response=classification.clarification_prompt if clarifying else "",
            routing_target=decision.routing_target,
            timestamp=self._clock(),
        )

        # Step: update the CDT metrics and pointers.
        metrics = working.metrics.model_copy(
            update={
                "interaction_count": working.metrics.interaction_count + 1,
                "human_intervention_count": (
                    working.metrics.human_intervention_count + (1 if clarifying else 0)
                ),
            }
        )
        working = working.model_copy(
            update={
                "metrics": metrics,
                "active_interaction_id": interaction.interaction_id,
                "last_activity": self._clock(),
                "last_modified": self._clock(),
                "version_number": working.version_number + 1,
            }
        )

        # Step: awaiting clarification pauses execution (ACTIVE -> WAITING).
        if clarifying:
            working = transition(
                working, ConversationState.WAITING, reason="awaiting clarification"
            )

        # Step: persist with optimistic concurrency against the loaded version.
        self._store.save(working, expected_version=expected_version)

        # Step: dispatch events.
        if clarifying:
            self._emit(ConversationEventType.CLARIFICATION_REQUESTED, working)
        else:
            self._emit(ConversationEventType.RESPONSE_GENERATED, working)

        logger.info(
            "interaction_handled",
            extra={
                "conversation_id": conversation_id,
                "intent": classification.intent,
                "scope": classification.scope,
                "requires_clarification": clarifying,
                "routing_target": decision.routing_target,
            },
        )
        return InteractionResult(
            conversation=working, interaction=interaction, decision=decision
        )

    def _activate(self, cdt: ConversationDigitalTwin) -> ConversationDigitalTwin:
        if cdt.current_state is ConversationState.CREATED:
            return transition(cdt, ConversationState.ACTIVE, reason="first interaction")
        if cdt.current_state is ConversationState.WAITING:
            return transition(
                cdt, ConversationState.ACTIVE, reason="user response received"
            )
        return cdt

    def _emit(
        self, event_type: ConversationEventType, cdt: ConversationDigitalTwin
    ) -> None:
        if self._event_sink is None or not self._enable_events:
            return
        self._event_sink.publish(
            build_event(
                event_type,
                conversation_id=cdt.conversation_id,
                tenant_id=cdt.tenant_id,
                detail={"state": cdt.current_state},
            )
        )

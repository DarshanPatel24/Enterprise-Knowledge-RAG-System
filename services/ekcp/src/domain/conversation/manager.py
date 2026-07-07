"""Conversation administration: create, load, and close conversations.

The manager is the authoritative administration interface for conversation
lifecycle. It assigns identity, seeds the Conversation Digital Twin, and applies
governed lifecycle transitions (close, archive, pause, resume) while persisting
through the store with optimistic concurrency.
"""

from __future__ import annotations

import uuid

from domain.conversation.events import (
    ConversationEventType,
    EventSink,
    build_event,
)
from domain.conversation.lifecycle import transition
from domain.conversation.models import (
    ConversationDigitalTwin,
    ConversationState,
    OwnershipModel,
)
from domain.conversation.policy import ConversationPolicy
from domain.conversation.store import ConversationStore


def _new_conversation_id() -> str:
    """Return a fresh globally-unique conversation id."""
    return f"conv-{uuid.uuid4().hex[:12]}"


class ConversationManager:
    """Create, load, and transition conversations through their lifecycle."""

    def __init__(
        self,
        store: ConversationStore,
        *,
        policy: ConversationPolicy,
        event_sink: EventSink | None = None,
    ) -> None:
        self._store = store
        self._policy = policy
        self._event_sink = event_sink

    def create(
        self,
        *,
        tenant_id: str,
        owner_id: str,
        title: str,
        workspace_id: str | None = None,
        participants: tuple[str, ...] = (),
        security_classification: str = "internal",
        ownership_model: OwnershipModel = OwnershipModel.INDIVIDUAL,
        session_id: str | None = None,
    ) -> ConversationDigitalTwin:
        """Create a new conversation in the CREATED state and persist it."""
        cdt = ConversationDigitalTwin(
            conversation_id=_new_conversation_id(),
            workspace_id=workspace_id or self._policy.default_workspace_id,
            tenant_id=tenant_id,
            title=title,
            owner_id=owner_id,
            participants=participants or (owner_id,),
            priority=self._policy.default_priority,
            security_classification=security_classification,
            language=self._policy.default_language,
            ownership_model=ownership_model,
            active_session_ids=(session_id,) if session_id else (),
        )
        self._store.save(cdt, expected_version=None)
        self._emit(ConversationEventType.CONVERSATION_CREATED, cdt)
        return cdt

    def get(self, tenant_id: str, conversation_id: str) -> ConversationDigitalTwin:
        """Return the current CDT for a conversation."""
        return self._store.get(tenant_id, conversation_id)

    def complete(self, tenant_id: str, conversation_id: str) -> ConversationDigitalTwin:
        """Transition a conversation to COMPLETED (and ARCHIVED per policy)."""
        cdt = self._store.get(tenant_id, conversation_id)
        expected = cdt.version_number
        updated = transition(cdt, ConversationState.COMPLETED, reason="objective met")
        self._store.save(updated, expected_version=expected)
        self._emit(ConversationEventType.CONVERSATION_COMPLETED, updated)
        if self._policy.archive_on_complete:
            expected = updated.version_number
            archived = transition(
                updated, ConversationState.ARCHIVED, reason="archived on complete"
            )
            self._store.save(archived, expected_version=expected)
            self._emit(ConversationEventType.CONVERSATION_ARCHIVED, archived)
            return archived
        return updated

    def pause(self, tenant_id: str, conversation_id: str) -> ConversationDigitalTwin:
        """Transition an active conversation to PAUSED."""
        cdt = self._store.get(tenant_id, conversation_id)
        expected = cdt.version_number
        updated = transition(cdt, ConversationState.PAUSED, reason="user paused")
        self._store.save(updated, expected_version=expected)
        self._emit(ConversationEventType.CONVERSATION_PAUSED, updated)
        return updated

    def resume(self, tenant_id: str, conversation_id: str) -> ConversationDigitalTwin:
        """Transition a paused conversation back to ACTIVE."""
        cdt = self._store.get(tenant_id, conversation_id)
        expected = cdt.version_number
        updated = transition(cdt, ConversationState.ACTIVE, reason="user resumed")
        self._store.save(updated, expected_version=expected)
        self._emit(ConversationEventType.CONVERSATION_RESUMED, updated)
        return updated

    def _emit(
        self, event_type: ConversationEventType, cdt: ConversationDigitalTwin
    ) -> None:
        if self._event_sink is None or not self._policy.enable_events:
            return
        self._event_sink.publish(
            build_event(
                event_type,
                conversation_id=cdt.conversation_id,
                tenant_id=cdt.tenant_id,
                detail={"state": cdt.current_state},
            )
        )

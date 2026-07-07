"""Conversation persistence with optimistic concurrency.

The store persists the immutable Conversation Digital Twin keyed by
``(tenant_id, conversation_id)``. Saves are guarded by the expected version so
concurrent writers cannot silently overwrite each other; a mismatch raises a
version conflict. The in-memory store is the local-first offline default; the
Microsoft SQL Server control plane is wired behind the same interface later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.conversation.errors import ConversationError, ConversationErrorType
from domain.conversation.models import ConversationDigitalTwin


class ConversationStore(ABC):
    """Abstract conversation persistence keyed by tenant and conversation id."""

    @abstractmethod
    def get(self, tenant_id: str, conversation_id: str) -> ConversationDigitalTwin:
        """Return the stored CDT, or raise ``NOT_FOUND``."""

    @abstractmethod
    def save(
        self, cdt: ConversationDigitalTwin, *, expected_version: int | None
    ) -> None:
        """Persist ``cdt`` guarded by ``expected_version`` (None for create)."""


class InMemoryConversationStore(ConversationStore):
    """Deterministic in-memory conversation store (local-first default)."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], ConversationDigitalTwin] = {}

    def get(self, tenant_id: str, conversation_id: str) -> ConversationDigitalTwin:
        cdt = self._items.get((tenant_id, conversation_id))
        if cdt is None:
            raise ConversationError(
                ConversationErrorType.NOT_FOUND,
                f"conversation {conversation_id} not found for tenant {tenant_id}",
            )
        return cdt

    def save(
        self, cdt: ConversationDigitalTwin, *, expected_version: int | None
    ) -> None:
        key = (cdt.tenant_id, cdt.conversation_id)
        existing = self._items.get(key)
        if expected_version is None:
            if existing is not None:
                raise ConversationError(
                    ConversationErrorType.ALREADY_EXISTS,
                    f"conversation {cdt.conversation_id} already exists",
                )
        else:
            if existing is None:
                raise ConversationError(
                    ConversationErrorType.NOT_FOUND,
                    f"conversation {cdt.conversation_id} not found",
                )
            if existing.version_number != expected_version:
                raise ConversationError(
                    ConversationErrorType.VERSION_CONFLICT,
                    (
                        f"version conflict for {cdt.conversation_id}: "
                        f"expected {expected_version}, found {existing.version_number}"
                    ),
                )
        self._items[key] = cdt

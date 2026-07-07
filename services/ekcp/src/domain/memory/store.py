"""Memory persistence.

The store persists immutable memory items keyed by ``(tenant_id, memory_id)`` and
supports scoped listing for retrieval, consolidation, and retention. The
in-memory store is the local-first offline default; a durable store (control
plane plus vector index) is wired behind this interface in a later sprint.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from domain.memory.errors import MemoryError, MemoryErrorType
from domain.memory.models import MemoryItem, MemoryScope, MemoryStatus


class MemoryStore(ABC):
    """Abstract memory persistence keyed by tenant and memory id."""

    @abstractmethod
    def save(self, item: MemoryItem) -> None:
        """Persist (insert or replace) a memory item."""

    @abstractmethod
    def get(self, tenant_id: str, memory_id: str) -> MemoryItem:
        """Return the memory item, or raise ``NOT_FOUND``."""

    @abstractmethod
    def delete(self, tenant_id: str, memory_id: str) -> None:
        """Hard-delete a memory item (right-to-be-forgotten)."""

    @abstractmethod
    def list_for(
        self,
        tenant_id: str,
        *,
        scopes: Sequence[MemoryScope] | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
        status: MemoryStatus | None = MemoryStatus.ACTIVE,
    ) -> list[MemoryItem]:
        """Return items for a tenant filtered by scope, conversation, user, status."""


class InMemoryMemoryStore(MemoryStore):
    """Deterministic in-memory memory store (local-first default)."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], MemoryItem] = {}

    def save(self, item: MemoryItem) -> None:
        self._items[(item.tenant_id, item.memory_id)] = item

    def get(self, tenant_id: str, memory_id: str) -> MemoryItem:
        item = self._items.get((tenant_id, memory_id))
        if item is None:
            raise MemoryError(
                MemoryErrorType.NOT_FOUND,
                f"memory {memory_id} not found for tenant {tenant_id}",
            )
        return item

    def delete(self, tenant_id: str, memory_id: str) -> None:
        self._items.pop((tenant_id, memory_id), None)

    def list_for(
        self,
        tenant_id: str,
        *,
        scopes: Sequence[MemoryScope] | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
        status: MemoryStatus | None = MemoryStatus.ACTIVE,
    ) -> list[MemoryItem]:
        scope_set = set(scopes) if scopes is not None else None
        result: list[MemoryItem] = []
        for (item_tenant, _), item in self._items.items():
            if item_tenant != tenant_id:
                continue
            if scope_set is not None and item.scope not in scope_set:
                continue
            if conversation_id is not None and item.conversation_id != conversation_id:
                continue
            if user_id is not None and item.user_id != user_id:
                continue
            if status is not None and item.status is not status:
                continue
            result.append(item)
        result.sort(key=lambda i: i.created_at)
        return result

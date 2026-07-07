"""Memory retention and right-to-be-forgotten enforcement (handbook 8.20, Ch 12).

Applies per-scope TTLs, expires items whose retention window has passed, and
hard-deletes items for a user or conversation to satisfy deletion requests.
Enforcement is deterministic under an injected clock.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from domain.memory.models import MemoryItem, MemoryScope, MemoryStatus
from domain.memory.policy import MemoryPolicy
from domain.memory.store import MemoryStore


def resolve_expiry(
    policy: MemoryPolicy, scope: MemoryScope, created_at: datetime
) -> datetime | None:
    """Return the expiration timestamp for a scope, or None for indefinite retention."""
    ttl = policy.scope_ttl_seconds(scope)
    if ttl is None:
        return None
    return created_at + timedelta(seconds=ttl)


class RetentionEnforcer:
    """Expire aged memories and purge memories for deletion requests."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def expire(self, tenant_id: str, *, now: datetime) -> int:
        """Mark active memories past their expiration as expired; return the count."""
        expired = 0
        for item in self._store.list_for(tenant_id, status=MemoryStatus.ACTIVE):
            if item.is_expired(now=now):
                self._store.save(
                    item.model_copy(
                        update={"status": MemoryStatus.EXPIRED, "updated_at": now}
                    )
                )
                expired += 1
        return expired

    def purge(
        self,
        tenant_id: str,
        *,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> int:
        """Hard-delete memories for a user or conversation; return the count."""
        targets: list[MemoryItem] = []
        for status in MemoryStatus:
            targets.extend(
                self._store.list_for(
                    tenant_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    status=status,
                )
            )
        seen: set[str] = set()
        deleted = 0
        for item in targets:
            if item.memory_id in seen:
                continue
            seen.add(item.memory_id)
            self._store.delete(tenant_id, item.memory_id)
            deleted += 1
        return deleted

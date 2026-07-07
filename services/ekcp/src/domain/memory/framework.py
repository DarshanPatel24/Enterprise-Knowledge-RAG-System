"""Memory framework facade: remember, recall, consolidate, forget, expire.

The single production entry point for memory. It creates governed memory items
with confidence and per-scope retention, retrieves ranked memories (exposable as
context items for the assembler), consolidates active memories into long-term
summaries, and enforces expiration and right-to-be-forgotten deletion.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from domain.context import ContextItem
from domain.memory.compression import summarize
from domain.memory.confidence import confidence_for
from domain.memory.errors import MemoryError, MemoryErrorType
from domain.memory.models import (
    CompressionLevel,
    MemoryItem,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    ScoredMemory,
    ValidationMethod,
)
from domain.memory.policy import MemoryPolicy
from domain.memory.retention import RetentionEnforcer, resolve_expiry
from domain.memory.retrieval import (
    MemoryRetriever,
    default_recall_scopes,
    to_context_items,
)
from domain.memory.store import MemoryStore
from domain.observability import get_logger

logger = get_logger("ekcp.memory")


class MemoryFramework:
    """Governed memory: creation, retrieval, consolidation, and retention."""

    def __init__(
        self,
        store: MemoryStore,
        policy: MemoryPolicy,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._policy = policy
        self._retriever = MemoryRetriever(policy)
        self._retention = RetentionEnforcer(store)
        self._clock = clock or (lambda: datetime.now(UTC))

    def remember(
        self,
        *,
        tenant_id: str,
        content: str,
        memory_type: MemoryType,
        scope: MemoryScope,
        validation_method: ValidationMethod,
        topic: str = "",
        tags: tuple[str, ...] = (),
        classification: str | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
        workspace_id: str | None = None,
        source_interaction_id: str | None = None,
    ) -> MemoryItem:
        """Create, govern, and persist a memory item."""
        now = self._clock()
        item = MemoryItem(
            memory_id=f"mem-{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            scope=scope,
            content=content,
            memory_type=memory_type,
            topic=topic,
            tags=tags,
            confidence=confidence_for(validation_method),
            classification=classification or self._policy.default_classification,
            source_validation_method=validation_method,
            source_conversation_id=conversation_id,
            source_interaction_id=source_interaction_id,
            conversation_id=conversation_id,
            user_id=user_id,
            workspace_id=workspace_id,
            created_at=now,
            updated_at=now,
            expires_at=resolve_expiry(self._policy, scope, now),
        )
        self._store.save(item)
        logger.info(
            "memory_stored",
            extra={"memory_id": item.memory_id, "scope": scope, "tenant_id": tenant_id},
        )
        return item

    def recall(
        self,
        *,
        tenant_id: str,
        query: str,
        scopes: Sequence[MemoryScope] | None = None,
        limit: int | None = None,
        min_confidence: float | None = None,
        record_usage: bool = True,
    ) -> list[ScoredMemory]:
        """Retrieve ranked memories for a query, updating usage counters."""
        now = self._clock()
        search_scopes = tuple(scopes) if scopes is not None else default_recall_scopes()
        candidates = self._store.list_for(tenant_id, scopes=search_scopes)
        ranked = self._retriever.rank(
            candidates, query=query, now=now, min_confidence=min_confidence, limit=limit
        )
        if not record_usage:
            return ranked
        updated: list[ScoredMemory] = []
        for entry in ranked:
            touched = entry.item.model_copy(
                update={
                    "retrieval_count": entry.item.retrieval_count + 1,
                    "last_retrieved_at": now,
                }
            )
            self._store.save(touched)
            updated.append(entry.model_copy(update={"item": touched}))
        return updated

    def recall_as_context(
        self,
        *,
        tenant_id: str,
        query: str,
        scopes: Sequence[MemoryScope] | None = None,
        limit: int | None = None,
        min_confidence: float | None = None,
    ) -> tuple[ContextItem, ...]:
        """Retrieve ranked memories as context items for the assembler (S2)."""
        return to_context_items(
            self.recall(
                tenant_id=tenant_id,
                query=query,
                scopes=scopes,
                limit=limit,
                min_confidence=min_confidence,
                record_usage=False,
            )
        )

    def consolidate(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        level: CompressionLevel = CompressionLevel.SUMMARY,
    ) -> MemoryItem:
        """Consolidate a conversation's active memories into a long-term summary."""
        sources = [
            item
            for item in self._store.list_for(
                tenant_id,
                conversation_id=conversation_id,
                scopes=(MemoryScope.WORKING, MemoryScope.SESSION, MemoryScope.CONVERSATION),
            )
        ]
        if not sources:
            raise MemoryError(
                MemoryErrorType.NOTHING_TO_CONSOLIDATE,
                f"no active memories to consolidate for conversation {conversation_id}",
            )
        now = self._clock()
        best = max(sources, key=lambda item: item.confidence)
        consolidated = MemoryItem(
            memory_id=f"mem-{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            scope=MemoryScope.CONVERSATION,
            content=summarize(sources, level=level),
            memory_type=MemoryType.INSIGHT,
            topic="conversation_summary",
            confidence=best.confidence,
            classification=best.classification,
            source_validation_method=best.source_validation_method,
            source_conversation_id=conversation_id,
            conversation_id=conversation_id,
            user_id=best.user_id,
            related_memories=tuple(item.memory_id for item in sources),
            created_at=now,
            updated_at=now,
            expires_at=resolve_expiry(self._policy, MemoryScope.CONVERSATION, now),
        )
        self._store.save(consolidated)
        for item in sources:
            self._store.save(
                item.model_copy(
                    update={"status": MemoryStatus.ARCHIVED, "updated_at": now}
                )
            )
        logger.info(
            "memory_consolidated",
            extra={
                "memory_id": consolidated.memory_id,
                "sources": len(sources),
                "compression_level": level,
            },
        )
        return consolidated

    def expire(self, *, tenant_id: str) -> int:
        """Expire memories whose retention window has passed."""
        return self._retention.expire(tenant_id, now=self._clock())

    def forget(
        self,
        *,
        tenant_id: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> int:
        """Hard-delete memories for a user or conversation (right-to-be-forgotten)."""
        deleted = self._retention.purge(
            tenant_id, user_id=user_id, conversation_id=conversation_id
        )
        logger.info(
            "memory_forgotten",
            extra={"tenant_id": tenant_id, "deleted": deleted},
        )
        return deleted

    def get(self, tenant_id: str, memory_id: str) -> MemoryItem:
        """Return a memory item by id."""
        return self._store.get(tenant_id, memory_id)

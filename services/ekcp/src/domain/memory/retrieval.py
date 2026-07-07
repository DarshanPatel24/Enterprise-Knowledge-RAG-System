"""Memory retrieval: deterministic multi-dimensional relevance ranking.

Ranks candidate memories by a weighted blend of relevance, recency, importance,
frequency, and trust (handbook 6.9, 8.17). Retrieval is deterministic under an
injected clock and integrates with context orchestration by exposing the ranked
memories as :class:`ContextItem` objects for the assembler (S2).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from domain.context import ContextItem, ContextSource
from domain.memory.models import (
    MemoryItem,
    MemoryScope,
    MemoryType,
    ScoredMemory,
)
from domain.memory.policy import MemoryPolicy

# Business importance weight by memory type.
_TYPE_IMPORTANCE: dict[MemoryType, float] = {
    MemoryType.DECISION: 1.0,
    MemoryType.PREFERENCE: 0.9,
    MemoryType.PROCEDURE: 0.85,
    MemoryType.FACT: 0.8,
    MemoryType.INSIGHT: 0.75,
    MemoryType.RELATIONSHIP: 0.7,
}


def _tokens(text: str) -> set[str]:
    return {token for token in text.lower().split() if token}


class MemoryRetriever:
    """Rank memories by weighted relevance for a query."""

    def __init__(self, policy: MemoryPolicy) -> None:
        self._policy = policy

    def rank(
        self,
        items: Sequence[MemoryItem],
        *,
        query: str,
        now: datetime,
        min_confidence: float | None = None,
        limit: int | None = None,
    ) -> list[ScoredMemory]:
        """Return the ranked, filtered memories for a query."""
        threshold = (
            min_confidence
            if min_confidence is not None
            else self._policy.default_min_confidence
        )
        query_tokens = _tokens(query)
        scored: list[ScoredMemory] = []
        for item in items:
            if item.is_expired(now=now) or item.confidence < threshold:
                continue
            score = self._score(item, query_tokens=query_tokens, now=now)
            scored.append(ScoredMemory(item=item, score=round(score, 6)))
        scored.sort(
            key=lambda s: (-s.score, s.item.created_at, s.item.memory_id)
        )
        cap = limit if limit is not None else self._policy.max_retrieval_limit
        return scored[:cap]

    def _score(
        self, item: MemoryItem, *, query_tokens: set[str], now: datetime
    ) -> float:
        weights = self._policy.retrieval_weights()
        relevance = self._relevance(item, query_tokens)
        recency = self._recency(item, now)
        importance = _TYPE_IMPORTANCE[item.memory_type]
        frequency = min(1.0, item.retrieval_count / 10.0)
        trust = item.confidence
        total = (
            weights["relevance"] * relevance
            + weights["recency"] * recency
            + weights["importance"] * importance
            + weights["frequency"] * frequency
            + weights["trust"] * trust
        )
        weight_sum = sum(weights.values()) or 1.0
        return max(0.0, min(1.0, total / weight_sum))

    @staticmethod
    def _relevance(item: MemoryItem, query_tokens: set[str]) -> float:
        if not query_tokens:
            return 0.5
        corpus = _tokens(item.content) | _tokens(item.topic) | {t.lower() for t in item.tags}
        if not corpus:
            return 0.0
        overlap = len(query_tokens & corpus)
        return overlap / len(query_tokens)

    def _recency(self, item: MemoryItem, now: datetime) -> float:
        age_hours = max(0.0, (now - item.created_at).total_seconds() / 3600.0)
        half_life = self._policy.recency_half_life_hours
        return float(0.5 ** (age_hours / half_life))


def to_context_items(scored: Sequence[ScoredMemory]) -> tuple[ContextItem, ...]:
    """Convert ranked memories into context items for the assembler (S2)."""
    return tuple(
        ContextItem(
            source=ContextSource.MEMORY,
            content=entry.item.content,
            reason=f"memory:{entry.item.scope}:{entry.item.memory_type}",
            rank_score=entry.score,
        )
        for entry in scored
    )


def default_recall_scopes() -> tuple[MemoryScope, ...]:
    """Return the default scopes searched for a personal recall query."""
    return (
        MemoryScope.WORKING,
        MemoryScope.SESSION,
        MemoryScope.CONVERSATION,
        MemoryScope.USER,
    )

"""Context assembler: build the governed Execution Context Package.

Implements the handbook assembly pipeline (Collect -> Rank -> Filter -> Govern ->
Budget -> Package). Context is assembled from conversation history, enterprise
knowledge (EKRE retrieval), memory, tool outputs, and policy constraints, ranked
by relevance and recency, deduplicated, citation-checked, and bounded to a token
budget with graceful degradation. Assembly is deterministic and never generates.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from contracts.retrieval import RetrievalContextPackage
from domain.context.models import (
    ContextItem,
    ContextLineageItem,
    ContextMetrics,
    ContextSource,
    ExecutionContextPackage,
    PolicyStatus,
)
from domain.context.policy import ContextPolicy
from domain.context.tokens import estimate_tokens
from domain.observability import get_logger

logger = get_logger("ekcp.context.assembler")

# Deterministic tie-break ordering across sources.
_SOURCE_ORDER: dict[ContextSource, int] = {
    ContextSource.POLICY: 0,
    ContextSource.ENTERPRISE: 1,
    ContextSource.CONVERSATION: 2,
    ContextSource.MEMORY: 3,
    ContextSource.TOOL: 4,
    ContextSource.WORKSPACE: 5,
    ContextSource.AGENT: 6,
}


class ContextAssembler:
    """Assemble ranked, governed, token-bounded context before generation."""

    def __init__(self, policy: ContextPolicy) -> None:
        self._policy = policy

    def assemble(
        self,
        *,
        tenant_id: str,
        conversation_id: str,
        user_intent: str,
        conversation_history: Sequence[str] = (),
        retrieval: RetrievalContextPackage | None = None,
        memory_items: Sequence[ContextItem] = (),
        tool_items: Sequence[ContextItem] = (),
        policy_items: Sequence[ContextItem] = (),
    ) -> ExecutionContextPackage:
        """Assemble the Execution Context Package for a conversation turn."""
        warnings: list[str] = []
        dropped_citation_unready = 0

        candidates: list[ContextItem] = []
        candidates.extend(self._conversation_items(conversation_history))
        enterprise, dropped_citation_unready = self._enterprise_items(retrieval)
        if dropped_citation_unready:
            warnings.append(
                f"dropped {dropped_citation_unready} enterprise item(s) with unready citations"
            )
        candidates.extend(enterprise)
        candidates.extend(self._scored(memory_items))
        candidates.extend(self._scored(tool_items))
        forced = self._scored(policy_items, force_source=ContextSource.POLICY)

        considered = len(candidates) + len(forced) + dropped_citation_unready

        # Relevance filter (policy items are always retained).
        ranked: list[ContextItem] = []
        dropped_below_relevance = 0
        for item in candidates:
            if item.rank_score < self._policy.min_relevance:
                dropped_below_relevance += 1
                continue
            ranked.append(item)

        # Deduplicate by normalized content, keeping the higher-ranked instance.
        dropped_duplicates = 0
        if self._policy.dedupe_content:
            ranked, dropped_duplicates = self._dedupe(ranked)

        ranked.sort(key=lambda i: (_SOURCE_ORDER[i.source], -i.rank_score, i.content))

        # Token budget: policy items first, then ranked items with degradation.
        selected, total_tokens, dropped_for_budget = self._apply_budget(forced, ranked)

        lineage = tuple(
            ContextLineageItem(
                source=item.source,
                reason=item.reason,
                rank_score=item.rank_score,
                policy_status=item.policy_status,
            )
            for item in selected
        )
        metrics = ContextMetrics(
            considered_count=considered,
            selected_count=len(selected),
            dropped_for_budget=dropped_for_budget,
            dropped_below_relevance=dropped_below_relevance,
            dropped_duplicates=dropped_duplicates,
            dropped_citation_unready=dropped_citation_unready,
            total_tokens=total_tokens,
            token_budget=self._policy.effective_budget(),
            source_diversity=len({item.source for item in selected}),
        )
        package = ExecutionContextPackage(
            context_id=f"ctx-{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            user_intent=user_intent,
            items=tuple(selected),
            lineage=lineage,
            metrics=metrics,
            compression_applied=dropped_for_budget > 0,
            security_filtered=retrieval.security_filtered if retrieval else True,
            warnings=tuple(warnings),
        )
        logger.info(
            "context_assembled",
            extra={
                "conversation_id": conversation_id,
                "selected": len(selected),
                "total_tokens": total_tokens,
                "source_diversity": metrics.source_diversity,
            },
        )
        return package

    def _conversation_items(self, history: Sequence[str]) -> list[ContextItem]:
        items: list[ContextItem] = []
        count = len(history)
        for index, message in enumerate(history):
            text = message.strip()
            if not text:
                continue
            recency = (index + 1) / count if count else 1.0
            score = round(min(0.9, 0.4 + 0.4 * recency), 4)
            items.append(
                ContextItem(
                    source=ContextSource.CONVERSATION,
                    content=text,
                    reason="recent conversation message",
                    rank_score=score,
                    token_estimate=self._tokens(text),
                )
            )
        return items

    def _enterprise_items(
        self, retrieval: RetrievalContextPackage | None
    ) -> tuple[list[ContextItem], int]:
        if retrieval is None:
            return [], 0
        items: list[ContextItem] = []
        dropped = 0
        for candidate in retrieval.candidates:
            citation = candidate.citation
            content = candidate.content.strip()
            if not content or not self._citation_ready(citation):
                dropped += 1
                continue
            items.append(
                ContextItem(
                    source=ContextSource.ENTERPRISE,
                    content=content,
                    reason=candidate.explanation or "retrieved enterprise evidence",
                    rank_score=candidate.relevance_score,
                    citation=citation,
                    token_estimate=self._tokens(content),
                )
            )
        return items, dropped

    @staticmethod
    def _citation_ready(citation: object) -> bool:
        source_path = getattr(citation, "source_path", "")
        document_id = getattr(citation, "document_id", "")
        chunk_id = getattr(citation, "chunk_id", "")
        return bool(source_path and document_id and chunk_id)

    def _scored(
        self,
        items: Sequence[ContextItem],
        *,
        force_source: ContextSource | None = None,
    ) -> list[ContextItem]:
        result: list[ContextItem] = []
        for item in items:
            updates: dict[str, object] = {"token_estimate": self._tokens(item.content)}
            if force_source is not None:
                updates["source"] = force_source
                updates["policy_status"] = PolicyStatus.ALLOWED
            result.append(item.model_copy(update=updates))
        return result

    @staticmethod
    def _dedupe(items: list[ContextItem]) -> tuple[list[ContextItem], int]:
        seen: set[str] = set()
        kept: list[ContextItem] = []
        dropped = 0
        for item in sorted(items, key=lambda i: -i.rank_score):
            key = item.content.strip().lower()
            if key in seen:
                dropped += 1
                continue
            seen.add(key)
            kept.append(item)
        return kept, dropped

    def _apply_budget(
        self, forced: list[ContextItem], ranked: list[ContextItem]
    ) -> tuple[list[ContextItem], int, int]:
        budget = self._policy.effective_budget()
        selected: list[ContextItem] = []
        total = 0
        for item in forced:
            selected.append(item)
            total += item.token_estimate
        dropped = 0
        for item in ranked:
            if selected and total + item.token_estimate > budget:
                dropped += 1
                continue
            selected.append(item)
            total += item.token_estimate
        return selected, total, dropped

    def _tokens(self, text: str) -> int:
        return estimate_tokens(text, chars_per_token=self._policy.chars_per_token)

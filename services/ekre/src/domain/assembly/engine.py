"""Context Assembly Engine (handbook Chapters 26-27).

Transforms a Ranked Knowledge Set into the model-agnostic Retrieval Context
Package handed to EKCP: select within the token budget, organize into reading
order, build citation-preserving candidates, and package the immutable result
with auditable metrics. Assembly never retrieves, ranks, or modifies knowledge.
"""

from __future__ import annotations

from contracts.retrieval import RetrievalContextPackage
from domain.assembly.citations import to_candidate
from domain.assembly.models import AssemblyResult, ContextMetrics
from domain.assembly.policy import AssemblyPolicy
from domain.assembly.selection import ContextSelector, SelectedContext
from domain.observability import get_logger
from domain.ranking.models import RankedKnowledgeSet

_logger = get_logger("ekre.assembly")


class ContextAssemblyEngine:
    """Assembles ranked knowledge into the EKCP handoff package."""

    def __init__(self, policy: AssemblyPolicy) -> None:
        self._policy = policy
        self._selector = ContextSelector(policy)

    def assemble(
        self,
        rks: RankedKnowledgeSet,
        *,
        query: str,
        tenant_id: str,
        security_filtered: bool = True,
    ) -> AssemblyResult:
        """Select, organize, and package ranked knowledge for EKCP."""
        selection = self._selector.select(rks.objects)
        ordered = self._order(selection.selected)
        candidates = [to_candidate(item) for item in ordered]

        package = RetrievalContextPackage(
            query=query,
            tenant_id=tenant_id,
            candidates=candidates,
            security_filtered=security_filtered,
        )
        metrics = ContextMetrics(
            considered_count=len(rks.objects),
            selected_count=len(candidates),
            total_tokens=selection.total_tokens,
            token_budget=self._policy.max_context_tokens,
            dropped_for_budget=selection.dropped_for_budget,
            dropped_duplicates=selection.dropped_duplicates,
            dropped_below_relevance=selection.dropped_below_relevance,
            ordering=self._policy.ordering,
        )
        _logger.info(
            "context_assembled",
            extra={
                "selected": metrics.selected_count,
                "considered": metrics.considered_count,
                "total_tokens": metrics.total_tokens,
            },
        )
        return AssemblyResult(package=package, metrics=metrics, warnings=rks.warnings)

    def _order(
        self, selected: tuple[SelectedContext, ...]
    ) -> tuple[SelectedContext, ...]:
        """Arrange selected context into reading order (handbook 26.8)."""
        if self._policy.ordering == "document":
            return tuple(
                sorted(
                    selected,
                    key=lambda item: (
                        item.ranked.knowledge_object.citation.document_id,
                        item.ranked.knowledge_object.citation.chunk_id,
                    ),
                )
            )
        # Default: preserve the relevance (rank) order from the ranking engine.
        return selected

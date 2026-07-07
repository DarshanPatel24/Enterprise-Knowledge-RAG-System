"""Ranking Engine (handbook Chapter 25).

Consumes a Fused Knowledge Set and produces a deterministic, auditable Ranked
Knowledge Set: eligibility filtering, per-factor evidence scoring, configurable
weighted aggregation, optional LLM reranking (with deterministic fallback),
threshold + candidate-limit controls, and final rank assignment. Ranking never
retrieves or modifies knowledge.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domain.fusion.models import FusedKnowledgeSet, KnowledgeObject
from domain.ranking.models import RankedKnowledgeObject, RankedKnowledgeSet
from domain.ranking.policy import RankingPolicy
from domain.ranking.reranker import IdentityReranker, Reranker
from domain.ranking.scoring import (
    build_explanation,
    composite_score,
    factor_scores,
    is_eligible,
)


@dataclass(frozen=True)
class _Scored:
    obj: KnowledgeObject
    factors: dict[str, float]
    composite: float


class RankingEngine:
    """Deterministic, auditable ranking engine with optional LLM reranking."""

    def __init__(self, policy: RankingPolicy, *, reranker: Reranker | None = None) -> None:
        self._policy = policy
        self._reranker = reranker or IdentityReranker()

    def rank(self, fks: FusedKnowledgeSet, *, query: str = "") -> RankedKnowledgeSet:
        """Rank the fused knowledge set into an ordered Ranked Knowledge Set."""
        eligible = [obj for obj in fks.objects if is_eligible(obj)]
        considered = len(eligible)
        max_fusion = max((obj.fusion_score for obj in eligible), default=0.0)

        scored = [self._score(obj, max_fusion) for obj in eligible]
        scored = [s for s in scored if s.composite >= self._policy.min_composite_score]
        scored.sort(
            key=lambda s: (
                -s.composite,
                -s.obj.best_score,
                s.obj.citation.document_id,
                s.obj.citation.chunk_id,
            )
        )

        reranked = self._apply_rerank(scored, query)
        limited = reranked[: self._policy.candidate_limit]

        objects = tuple(
            self._to_ranked(scored_item, rank=index + 1, reranked=self._reranker.enabled)
            for index, scored_item in enumerate(limited)
        )
        return RankedKnowledgeSet(
            ranking_id=f"rks-{uuid.uuid4().hex[:12]}",
            policy_version=self._policy.policy_version,
            objects=objects,
            object_count=len(objects),
            considered_count=considered,
            reranked=self._reranker.enabled,
            warnings=fks.warnings,
        )

    def _score(self, obj: KnowledgeObject, max_fusion: float) -> _Scored:
        factors = factor_scores(obj, max_fusion=max_fusion)
        composite = composite_score(factors, self._policy.weights)
        return _Scored(obj=obj, factors=factors, composite=composite)

    def _apply_rerank(self, scored: list[_Scored], query: str) -> list[_Scored]:
        if not self._reranker.enabled or not scored:
            return scored
        by_id = {s.obj.knowledge_id: s for s in scored}
        items = [(s.obj.knowledge_id, s.obj.content) for s in scored]
        order = self._reranker.rerank(query, items)
        return [by_id[identifier] for identifier in order if identifier in by_id]

    def _to_ranked(
        self, scored: _Scored, *, rank: int, reranked: bool
    ) -> RankedKnowledgeObject:
        return RankedKnowledgeObject(
            knowledge_object=scored.obj,
            rank=rank,
            composite_score=scored.composite,
            factor_scores=scored.factors,
            factor_weights=dict(self._policy.weights),
            explanation=build_explanation(
                scored.factors, self._policy.weights, scored.composite
            ),
            reranked=reranked,
        )

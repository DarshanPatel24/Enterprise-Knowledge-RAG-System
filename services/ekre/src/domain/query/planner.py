"""Query Planner (handbook Chapter 13).

Transforms retrieval intent into a deterministic Retrieval Execution Plan: which
engines to run, candidate limits, timeouts, and the ranking strategy. The
planner never executes retrieval. Latency budgets are injected from settings so
no timeout is hardcoded.
"""

from __future__ import annotations

from domain.query.errors import QueryIntelligenceError, QueryIntelligenceErrorType
from domain.query.models import (
    IntentClassification,
    QueryEnrichment,
    QueryUnderstanding,
    RankingStrategy,
    RetrievalEngineType,
    RetrievalIntent,
    RetrievalPlan,
    RetrievalProfile,
    RetrievalStep,
)

# Intents that benefit from exact keyword matching alongside vector search.
_KEYWORD_INTENTS = frozenset(
    {RetrievalIntent.EXACT_LOOKUP, RetrievalIntent.NAVIGATION, RetrievalIntent.COMPARISON}
)


class QueryPlanner:
    """Deterministic Retrieval Execution Plan builder."""

    def __init__(self, *, vector_timeout_ms: float, total_timeout_ms: float) -> None:
        self._vector_timeout_ms = vector_timeout_ms
        self._total_timeout_ms = total_timeout_ms

    def plan(
        self,
        understanding: QueryUnderstanding,
        intent: IntentClassification,
        enrichment: QueryEnrichment,
    ) -> RetrievalPlan:
        """Build the execution plan from the understood, classified query."""
        engines = self._select_engines(understanding, intent)
        if not engines:
            raise QueryIntelligenceError(
                QueryIntelligenceErrorType.PLANNING_FAILED,
                "no retrieval engine selected for the query",
            )

        candidate_limit = intent.suggested_candidate_count
        steps = tuple(
            RetrievalStep(
                engine=engine,
                candidate_limit=candidate_limit,
                timeout_ms=self._vector_timeout_ms,
                parallel_group=0,
            )
            for engine in engines
        )
        ranking = self._ranking_strategy(understanding, intent, engines)

        return RetrievalPlan(
            plan_id=f"plan-{understanding.query_id}",
            profile=intent.suggested_profile,
            steps=steps,
            ranking_strategy=ranking,
            total_candidate_limit=candidate_limit * len(steps),
            total_timeout_ms=self._total_timeout_ms,
        )

    def _select_engines(
        self, understanding: QueryUnderstanding, intent: IntentClassification
    ) -> tuple[RetrievalEngineType, ...]:
        engines: list[RetrievalEngineType] = [RetrievalEngineType.VECTOR]
        wants_keyword = (
            intent.intent in _KEYWORD_INTENTS
            or bool(understanding.entities)
            or bool(understanding.enterprise_terms)
        )
        if wants_keyword:
            engines.append(RetrievalEngineType.KEYWORD)
        wants_metadata = (
            bool(understanding.metadata_filters)
            or intent.suggested_profile is RetrievalProfile.COMPLIANCE
        )
        if wants_metadata:
            engines.append(RetrievalEngineType.METADATA)
        return tuple(dict.fromkeys(engines))

    def _ranking_strategy(
        self,
        understanding: QueryUnderstanding,
        intent: IntentClassification,
        engines: tuple[RetrievalEngineType, ...],
    ) -> RankingStrategy:
        if (
            intent.suggested_profile is RetrievalProfile.COMPLIANCE
            or understanding.metadata_filters
        ):
            return RankingStrategy.METADATA_WEIGHTED
        if len(engines) > 1:
            return RankingStrategy.HYBRID
        return RankingStrategy.SEMANTIC

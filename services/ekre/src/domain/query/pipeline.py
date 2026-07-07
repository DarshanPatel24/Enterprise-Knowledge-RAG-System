"""Query Intelligence pipeline orchestrator.

Runs the deterministic Query Intelligence Domain stages in order --- Query
Understanding, Intent Classification, Enrichment, and Planning --- and assembles
the immutable :class:`StructuredQuery`, recording every transformation for
explainability. The optional LLM interpreter refines the understanding stage
only and always degrades to the deterministic result.
"""

from __future__ import annotations

import uuid

from domain.query.enrichment import QueryEnrichmentEngine
from domain.query.intent import IntentClassificationEngine
from domain.query.llm import QueryLlmInterpreter
from domain.query.models import (
    QueryUnderstanding,
    StructuredQuery,
    Transformation,
)
from domain.query.planner import QueryPlanner
from domain.query.understanding import QueryUnderstandingEngine


class QueryIntelligenceEngine:
    """Orchestrate the query intelligence pipeline into a StructuredQuery."""

    def __init__(
        self,
        understanding: QueryUnderstandingEngine,
        intent: IntentClassificationEngine,
        enrichment: QueryEnrichmentEngine,
        planner: QueryPlanner,
        *,
        llm_interpreter: QueryLlmInterpreter | None = None,
    ) -> None:
        self._understanding = understanding
        self._intent = intent
        self._enrichment = enrichment
        self._planner = planner
        self._llm_interpreter = llm_interpreter

    def analyze(
        self,
        raw_query: str,
        *,
        tenant_id: str,
        query_id: str | None = None,
        language: str | None = None,
    ) -> StructuredQuery:
        """Run the full pipeline and return the explainable StructuredQuery."""
        resolved_query_id = query_id or f"q-{uuid.uuid4().hex[:12]}"
        transformations: list[Transformation] = []

        understanding = self._understanding.run(
            raw_query, query_id=resolved_query_id, language=language
        )
        understanding = self._apply_llm(raw_query, understanding, transformations)
        transformations.append(
            Transformation(
                stage="understanding",
                description=(
                    f"normalized query via {understanding.source}; "
                    f"{len(understanding.entities)} entities, "
                    f"{len(understanding.metadata_filters)} metadata filters"
                ),
            )
        )

        intent = self._intent.classify(understanding)
        transformations.append(
            Transformation(
                stage="intent",
                description=(
                    f"intent={intent.intent.value} profile={intent.suggested_profile.value} "
                    f"complexity={intent.complexity.value}"
                ),
            )
        )

        enrichment = self._enrichment.enrich(understanding)
        transformations.append(
            Transformation(
                stage="enrichment",
                description=f"{len(enrichment.enriched_terms)} enriched terms",
            )
        )

        plan = self._planner.plan(understanding, intent, enrichment)
        transformations.append(
            Transformation(
                stage="planning",
                description=(
                    f"engines={[step.engine.value for step in plan.steps]} "
                    f"ranking={plan.ranking_strategy.value}"
                ),
            )
        )

        return StructuredQuery(
            query_id=resolved_query_id,
            tenant_id=tenant_id,
            understanding=understanding,
            intent=intent,
            enrichment=enrichment,
            plan=plan,
            transformations=tuple(transformations),
        )

    def _apply_llm(
        self,
        raw_query: str,
        understanding: QueryUnderstanding,
        transformations: list[Transformation],
    ) -> QueryUnderstanding:
        if self._llm_interpreter is None or not self._llm_interpreter.enabled:
            return understanding
        interpretation = self._llm_interpreter.interpret(raw_query)
        if interpretation is None:
            transformations.append(
                Transformation(
                    stage="llm_interpreter",
                    description="llm interpreter unavailable; kept deterministic understanding",
                )
            )
            return understanding

        merged_entities = tuple(
            dict.fromkeys([*understanding.entities, *interpretation.entities])
        )
        transformations.append(
            Transformation(
                stage="llm_interpreter",
                description="llm interpreter refined normalization and entities",
            )
        )
        return understanding.model_copy(
            update={
                "normalized_query": interpretation.normalized_query
                or understanding.normalized_query,
                "detected_language": interpretation.language
                or understanding.detected_language,
                "entities": merged_entities,
                "source": "llm",
            }
        )

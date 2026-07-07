"""Tests for the deterministic Query Planner."""

from __future__ import annotations

from config.settings import QueryIntelligenceSettings
from domain.query import (
    IntentClassificationEngine,
    QueryEnrichmentEngine,
    QueryPlanner,
    QueryPolicy,
    QueryUnderstandingEngine,
    RankingStrategy,
    RetrievalEngineType,
    default_vocabulary,
)


def _plan(query: str) -> object:
    policy = QueryPolicy.from_settings(QueryIntelligenceSettings(_env_file=None))
    vocabulary = default_vocabulary()
    understanding = QueryUnderstandingEngine(policy, vocabulary=vocabulary).run(
        query, query_id="q1"
    )
    intent = IntentClassificationEngine(policy).classify(understanding)
    enrichment = QueryEnrichmentEngine(vocabulary=vocabulary).enrich(understanding)
    planner = QueryPlanner(vector_timeout_ms=150.0, total_timeout_ms=500.0)
    return planner.plan(understanding, intent, enrichment)


def test_vector_always_selected() -> None:
    plan = _plan("some general topic")
    engines = [step.engine for step in plan.steps]
    assert RetrievalEngineType.VECTOR in engines


def test_keyword_added_for_entities() -> None:
    plan = _plan('find "Travel Policy"')
    engines = [step.engine for step in plan.steps]
    assert RetrievalEngineType.KEYWORD in engines


def test_metadata_and_weighted_ranking_for_compliance() -> None:
    plan = _plan("policy regarding GDPR")
    engines = [step.engine for step in plan.steps]
    assert RetrievalEngineType.METADATA in engines
    assert plan.ranking_strategy is RankingStrategy.METADATA_WEIGHTED


def test_metadata_filter_triggers_metadata_engine() -> None:
    plan = _plan("architecture after:2024")
    engines = [step.engine for step in plan.steps]
    assert RetrievalEngineType.METADATA in engines


def test_plan_carries_timeouts_and_id() -> None:
    plan = _plan("some general topic")
    assert plan.plan_id == "plan-q1"
    assert plan.total_timeout_ms == 500.0
    assert all(step.timeout_ms == 150.0 for step in plan.steps)

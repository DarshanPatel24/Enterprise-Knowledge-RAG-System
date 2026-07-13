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


def _plan_hybrid(query: str) -> object:
    policy = QueryPolicy.from_settings(QueryIntelligenceSettings(_env_file=None))
    vocabulary = default_vocabulary()
    understanding = QueryUnderstandingEngine(policy, vocabulary=vocabulary).run(
        query, query_id="q1"
    )
    intent = IntentClassificationEngine(policy).classify(understanding)
    enrichment = QueryEnrichmentEngine(vocabulary=vocabulary).enrich(understanding)
    planner = QueryPlanner(
        vector_timeout_ms=150.0, total_timeout_ms=500.0, force_hybrid=True
    )
    return planner.plan(understanding, intent, enrichment)


def test_vector_always_selected() -> None:
    plan = _plan("some general topic")
    engines = [step.engine for step in plan.steps]
    assert RetrievalEngineType.VECTOR in engines


def test_force_hybrid_adds_keyword_for_plain_query() -> None:
    # Without force_hybrid a lowercase, entity-free query is vector-only.
    plain = [step.engine for step in _plan("integrity installation steps").steps]
    assert RetrievalEngineType.KEYWORD not in plain
    # With force_hybrid the lexical signal always participates.
    hybrid = [step.engine for step in _plan_hybrid("integrity installation steps").steps]
    assert RetrievalEngineType.KEYWORD in hybrid


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

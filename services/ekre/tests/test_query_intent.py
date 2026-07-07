"""Tests for the deterministic Intent Classification Engine."""

from __future__ import annotations

from config.settings import QueryIntelligenceSettings
from domain.query import (
    IntentClassificationEngine,
    QueryPolicy,
    QueryUnderstandingEngine,
    RetrievalIntent,
    RetrievalProfile,
    default_vocabulary,
)


def _policy() -> QueryPolicy:
    return QueryPolicy.from_settings(QueryIntelligenceSettings(_env_file=None))


def _classify(query: str) -> object:
    policy = _policy()
    understanding = QueryUnderstandingEngine(policy, vocabulary=default_vocabulary()).run(
        query, query_id="q1"
    )
    return IntentClassificationEngine(policy).classify(understanding)


def test_comparison_intent() -> None:
    result = _classify("compare EKIE and EKRE")
    assert result.intent is RetrievalIntent.COMPARISON
    assert result.suggested_profile is RetrievalProfile.BALANCED


def test_research_intent() -> None:
    result = _classify("everything about refinery shutdown")
    assert result.intent is RetrievalIntent.RESEARCH
    assert result.suggested_profile is RetrievalProfile.RECALL


def test_compliance_intent() -> None:
    result = _classify("policy regarding GDPR data retention")
    assert result.intent is RetrievalIntent.COMPLIANCE
    assert result.suggested_profile is RetrievalProfile.COMPLIANCE


def test_exact_lookup_intent() -> None:
    result = _classify("travel guide")
    assert result.intent is RetrievalIntent.EXACT_LOOKUP
    assert result.suggested_profile is RetrievalProfile.PRECISION
    assert result.suggested_candidate_count == 5


def test_default_intent_when_no_signal() -> None:
    result = _classify("quarterly refinery output numbers 2024")
    assert result.intent is RetrievalIntent.RESEARCH
    assert result.warnings


def test_classification_is_deterministic() -> None:
    first = _classify("compare EKIE and EKRE")
    second = _classify("compare EKIE and EKRE")
    assert first == second

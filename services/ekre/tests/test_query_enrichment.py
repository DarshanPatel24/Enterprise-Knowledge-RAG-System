"""Tests for the deterministic Query Enrichment Engine."""

from __future__ import annotations

from config.settings import QueryIntelligenceSettings
from domain.query import (
    QueryEnrichmentEngine,
    QueryPolicy,
    QueryUnderstandingEngine,
    default_vocabulary,
)


def _enrich(query: str) -> object:
    policy = QueryPolicy.from_settings(QueryIntelligenceSettings(_env_file=None))
    vocabulary = default_vocabulary()
    understanding = QueryUnderstandingEngine(policy, vocabulary=vocabulary).run(
        query, query_id="q1"
    )
    return QueryEnrichmentEngine(vocabulary=vocabulary).enrich(understanding)


def test_synonym_expansion() -> None:
    result = _enrich("travel policy document")
    terms = {expansion.term for expansion in result.expansions}
    assert "policy" in terms
    assert "guideline" in result.enriched_terms


def test_enterprise_terms_carried_into_enrichment() -> None:
    result = _enrich("vpn setup")
    assert "virtual private network" in result.enriched_terms


def test_no_expansion_when_no_known_terms() -> None:
    result = _enrich("xyztoken quarterly output")
    assert result.expansions == ()

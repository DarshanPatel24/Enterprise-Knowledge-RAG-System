"""Tests for the deterministic Query Understanding Engine."""

from __future__ import annotations

import pytest

from config.settings import QueryIntelligenceSettings
from domain.query import (
    QueryIntelligenceError,
    QueryIntelligenceErrorType,
    QueryPolicy,
    QueryUnderstandingEngine,
    default_vocabulary,
)


def _engine(*, max_length: int = 2048) -> QueryUnderstandingEngine:
    settings = QueryIntelligenceSettings(_env_file=None, max_query_length=max_length)
    policy = QueryPolicy.from_settings(settings)
    return QueryUnderstandingEngine(policy, vocabulary=default_vocabulary())


def _engine_with_products(products: dict[str, str]) -> QueryUnderstandingEngine:
    settings = QueryIntelligenceSettings(_env_file=None)
    policy = QueryPolicy.from_settings(settings)
    vocabulary = default_vocabulary().model_copy(update={"products": products})
    return QueryUnderstandingEngine(policy, vocabulary=vocabulary)


def test_normalizes_whitespace_and_quotes() -> None:
    result = _engine().run("  the   \u201cTravel Policy\u201d  ", query_id="q1")
    assert result.normalized_query == 'the "Travel Policy"'
    assert result.detected_language == "en"


def test_extracts_quoted_entity() -> None:
    result = _engine().run('find "Travel Policy" document', query_id="q1")
    assert "Travel Policy" in result.entities


def test_extracts_metadata_filter_with_operator() -> None:
    result = _engine().run("architecture after:2024", query_id="q1")
    assert result.metadata_filters[0].field == "after"
    assert result.metadata_filters[0].operator == "gte"
    assert result.metadata_filters[0].value == "2024"
    # Structured filter tokens are removed from the free-text query.
    assert "after:2024" not in result.normalized_query


def test_resolves_enterprise_acronym() -> None:
    result = _engine().run("VPN setup guide", query_id="q1")
    assert "virtual private network" in result.enterprise_terms


def _source_group_filters(result: object) -> list[str]:
    return [
        f.value
        for f in result.metadata_filters  # type: ignore[attr-defined]
        if f.field == "source_group"
    ]


def test_product_alias_maps_to_source_group_and_lowercases() -> None:
    result = _engine().run("priority mapping product:Cyber-Integrity", query_id="q1")
    assert _source_group_filters(result) == ["cyber-integrity"]
    assert "product:" not in result.normalized_query


def test_product_phrase_auto_scopes_to_source_group() -> None:
    engine = _engine_with_products({"cyber integrity": "cyber-integrity"})
    result = engine.run("cyber integrity installation steps", query_id="q1")
    assert _source_group_filters(result) == ["cyber-integrity"]


def test_explicit_product_filter_suppresses_auto_scope() -> None:
    engine = _engine_with_products({"cyber integrity": "cyber-integrity"})
    result = engine.run(
        "cyber integrity notes product:plantstate-integrity", query_id="q1"
    )
    assert _source_group_filters(result) == ["plantstate-integrity"]


def test_no_products_configured_adds_no_source_group_filter() -> None:
    result = _engine().run("cyber integrity installation steps", query_id="q1")
    assert _source_group_filters(result) == []


def test_parsed_product_groups_parses_pairs() -> None:
    settings = QueryIntelligenceSettings(
        _env_file=None,
        product_groups="Cyber Integrity=cyber-integrity; PlantState Integrity=plantstate-integrity",
    )
    assert settings.parsed_product_groups() == {
        "cyber integrity": "cyber-integrity",
        "plantstate integrity": "plantstate-integrity",
    }



def test_empty_query_raises() -> None:
    with pytest.raises(QueryIntelligenceError) as exc:
        _engine().run("   ", query_id="q1")
    assert exc.value.error_type is QueryIntelligenceErrorType.EMPTY_QUERY


def test_too_long_query_raises() -> None:
    with pytest.raises(QueryIntelligenceError) as exc:
        _engine(max_length=5).run("this query is far too long", query_id="q1")
    assert exc.value.error_type is QueryIntelligenceErrorType.QUERY_TOO_LONG

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


def test_empty_query_raises() -> None:
    with pytest.raises(QueryIntelligenceError) as exc:
        _engine().run("   ", query_id="q1")
    assert exc.value.error_type is QueryIntelligenceErrorType.EMPTY_QUERY


def test_too_long_query_raises() -> None:
    with pytest.raises(QueryIntelligenceError) as exc:
        _engine(max_length=5).run("this query is far too long", query_id="q1")
    assert exc.value.error_type is QueryIntelligenceErrorType.QUERY_TOO_LONG

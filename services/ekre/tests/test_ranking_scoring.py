"""Tests for ranking eligibility, evidence scoring, and aggregation."""

from __future__ import annotations

from _ranking_support import knowledge_object

from domain.query.models import RetrievalEngineType
from domain.ranking.scoring import (
    build_explanation,
    composite_score,
    coverage_score,
    distinctive_terms,
    factor_scores,
    is_eligible,
)


def test_ineligible_when_content_empty() -> None:
    obj = knowledge_object(
        "d1", "c1", [(RetrievalEngineType.VECTOR, 0.9, 0)], fusion_score=0.1, content="  "
    )
    assert is_eligible(obj) is False


def test_factor_scores_pick_engine_maxima() -> None:
    obj = knowledge_object(
        "d1",
        "c1",
        [(RetrievalEngineType.VECTOR, 0.9, 0), (RetrievalEngineType.KEYWORD, 0.5, 0)],
        fusion_score=0.2,
    )
    factors = factor_scores(obj, max_fusion=0.2)
    assert factors["semantic"] == 0.9
    assert factors["lexical"] == 0.5
    assert factors["metadata"] == 0.0
    assert factors["fusion"] == 1.0  # normalized against the set maximum


def test_composite_is_weighted_sum() -> None:
    factors = {"semantic": 1.0, "lexical": 0.0, "metadata": 0.0, "fusion": 0.0}
    weights = {"semantic": 0.4, "lexical": 0.2, "metadata": 0.1, "fusion": 0.3}
    assert composite_score(factors, weights) == 0.4


def test_explanation_lists_factor_contributions() -> None:
    factors = {"semantic": 0.9, "lexical": 0.0, "metadata": 0.0, "fusion": 1.0}
    weights = {"semantic": 0.4, "lexical": 0.2, "metadata": 0.1, "fusion": 0.3}
    explanation = build_explanation(factors, weights, 0.66)
    assert "semantic=0.900*0.40" in explanation
    assert "composite=0.6600" in explanation


def test_distinctive_terms_drops_function_words() -> None:
    terms = distinctive_terms("what are the steps for integrity installation, cyber integrity")
    assert "cyber" in terms
    assert "integrity" in terms
    assert "installation" in terms
    assert "the" not in terms
    assert "for" not in terms


def test_coverage_penalizes_missing_distinctive_term() -> None:
    terms = distinctive_terms("cyber integrity installation")
    present = knowledge_object(
        "cyber",
        "c1",
        [(RetrievalEngineType.VECTOR, 0.9, 0)],
        fusion_score=0.1,
        content="Cyber Integrity installation instructions",
    )
    missing = knowledge_object(
        "plantstate",
        "c1",
        [(RetrievalEngineType.VECTOR, 0.9, 0)],
        fusion_score=0.1,
        content="PlantState Integrity installation instructions",
    )
    assert coverage_score(present, terms) == 1.0
    assert coverage_score(missing, terms) < 1.0
    assert coverage_score(present, terms) > coverage_score(missing, terms)


def test_coverage_neutral_without_query_terms() -> None:
    obj = knowledge_object(
        "d1", "c1", [(RetrievalEngineType.VECTOR, 0.9, 0)], fusion_score=0.1
    )
    assert coverage_score(obj, frozenset()) == 1.0
    factors = factor_scores(obj, max_fusion=0.1)
    assert factors["coverage"] == 1.0

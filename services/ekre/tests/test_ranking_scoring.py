"""Tests for ranking eligibility, evidence scoring, and aggregation."""

from __future__ import annotations

from _ranking_support import knowledge_object

from domain.query.models import RetrievalEngineType
from domain.ranking.scoring import (
    build_explanation,
    composite_score,
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

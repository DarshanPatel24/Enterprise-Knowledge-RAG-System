"""Tests for the ranking engine (ordering, limits, audit fields)."""

from __future__ import annotations

from _ranking_support import fused_set, knowledge_object

from config.settings import RankingSettings
from domain.query.models import RetrievalEngineType
from domain.ranking import RankingEngine, RankingPolicy


def _engine(**overrides: object) -> RankingEngine:
    settings = RankingSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return RankingEngine(RankingPolicy.from_settings(settings))


def test_orders_by_composite_score() -> None:
    weak = knowledge_object(
        "d1", "c1", [(RetrievalEngineType.METADATA, 0.3, 0)], fusion_score=0.1
    )
    strong = knowledge_object(
        "d2",
        "c2",
        [(RetrievalEngineType.VECTOR, 0.95, 0), (RetrievalEngineType.KEYWORD, 0.8, 0)],
        fusion_score=0.2,
    )
    rks = _engine().rank(fused_set(weak, strong))
    assert rks.objects[0].knowledge_object.citation.document_id == "d2"
    assert rks.objects[0].rank == 1
    assert rks.objects[1].rank == 2


def test_audit_fields_present() -> None:
    obj = knowledge_object(
        "d1", "c1", [(RetrievalEngineType.VECTOR, 0.9, 0)], fusion_score=0.1
    )
    ranked = _engine().rank(fused_set(obj)).objects[0]
    assert set(ranked.factor_scores) == {
        "semantic",
        "lexical",
        "metadata",
        "fusion",
        "coverage",
    }
    assert ranked.factor_weights["semantic"] == 0.35
    assert "composite=" in ranked.explanation
    assert ranked.reranked is False


def test_coverage_lifts_document_that_names_the_query_term() -> None:
    # Two similarly named documents; only "cyber" distinguishes them. The vector
    # signal slightly favors the generic installation guide, but the coverage
    # factor must lift the document that actually names "cyber".
    plantstate = knowledge_object(
        "plantstate",
        "c1",
        [(RetrievalEngineType.VECTOR, 1.0, 0), (RetrievalEngineType.KEYWORD, 0.7, 1)],
        fusion_score=0.2,
        content="PlantState Integrity Installation Guide steps for integrity installation",
    )
    cyber = knowledge_object(
        "cyber",
        "c1",
        [(RetrievalEngineType.VECTOR, 0.9, 1), (RetrievalEngineType.KEYWORD, 1.0, 0)],
        fusion_score=0.19,
        content="Cyber Integrity Installation Guide steps for integrity installation",
    )
    rks = _engine().rank(
        fused_set(plantstate, cyber),
        query="what are the steps for integrity installation, cyber integrity",
    )
    assert rks.objects[0].knowledge_object.citation.document_id == "cyber"


def test_candidate_limit_applies() -> None:
    objs = [
        knowledge_object(
            f"d{i}", "c1", [(RetrievalEngineType.VECTOR, 0.9 - i * 0.1, 0)], fusion_score=0.1
        )
        for i in range(3)
    ]
    rks = _engine(candidate_limit=1).rank(fused_set(*objs))
    assert rks.object_count == 1
    assert rks.considered_count == 3


def test_min_score_filters_objects() -> None:
    obj = knowledge_object(
        "d1", "c1", [(RetrievalEngineType.METADATA, 0.05, 0)], fusion_score=0.0
    )
    rks = _engine(min_composite_score=0.9).rank(fused_set(obj))
    assert rks.object_count == 0
    assert rks.considered_count == 1


def test_ranking_is_deterministic() -> None:
    objs = [
        knowledge_object("d1", "c1", [(RetrievalEngineType.VECTOR, 0.9, 0)], fusion_score=0.2),
        knowledge_object("d2", "c2", [(RetrievalEngineType.KEYWORD, 0.7, 0)], fusion_score=0.1),
    ]
    first = _engine().rank(fused_set(*objs))
    second = _engine().rank(fused_set(*objs))
    assert first.objects == second.objects

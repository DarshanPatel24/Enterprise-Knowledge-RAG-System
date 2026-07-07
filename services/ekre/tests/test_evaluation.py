"""Tests for retrieval accuracy metrics and the evaluation harness."""

from __future__ import annotations

import math

from domain.evaluation import (
    QueryJudgment,
    evaluate,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_precision_and_recall_at_k() -> None:
    retrieved = ["a", "b", "c", "d"]
    relevant = frozenset({"a", "c", "x"})
    assert precision_at_k(retrieved, relevant, 4) == 0.5  # a, c in top 4
    assert recall_at_k(retrieved, relevant, 4) == 2 / 3  # 2 of 3 relevant found


def test_reciprocal_rank() -> None:
    assert reciprocal_rank(["x", "a"], frozenset({"a"})) == 0.5
    assert reciprocal_rank(["a"], frozenset({"a"})) == 1.0
    assert reciprocal_rank(["x", "y"], frozenset({"a"})) == 0.0


def test_ndcg_perfect_and_partial() -> None:
    # Perfect ranking -> NDCG 1.0.
    assert ndcg_at_k(["a", "b"], frozenset({"a", "b"}), 2) == 1.0
    # One relevant at rank 2 only.
    ndcg = ndcg_at_k(["x", "a"], frozenset({"a"}), 2)
    assert math.isclose(ndcg, 1.0 / math.log2(3), rel_tol=1e-9)


def test_evaluate_aggregates_and_checks_thresholds() -> None:
    judgments = [
        QueryJudgment(query_id="q1", relevant_ids=frozenset({"a"})),
        QueryJudgment(query_id="q2", relevant_ids=frozenset({"b"})),
    ]
    results = {"q1": ["a", "z"], "q2": ["z", "b"]}
    report = evaluate(
        judgments,
        results,
        k=2,
        thresholds={"precision": 0.2, "recall": 0.5, "mrr": 0.5, "ndcg": 0.5},
    )
    assert report.query_count == 2
    assert report.mean_reciprocal_rank == 0.75  # (1.0 + 0.5) / 2
    assert report.meets_thresholds is True


def test_evaluate_fails_thresholds_when_below() -> None:
    judgments = [QueryJudgment(query_id="q1", relevant_ids=frozenset({"a"}))]
    report = evaluate(
        judgments, {"q1": ["z", "y"]}, k=2, thresholds={"precision": 0.5}
    )
    assert report.mean_precision_at_k == 0.0
    assert report.meets_thresholds is False

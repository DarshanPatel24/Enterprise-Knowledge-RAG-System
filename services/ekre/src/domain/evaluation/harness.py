"""Evaluation models and harness (handbook Chapter 5 NFR validation).

Aggregates per-query ranking metrics into a report and checks them against the
configured accuracy thresholds. Deterministic; used offline to validate
retrieval accuracy before EKCP handoff.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from domain.evaluation.metrics import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class QueryJudgment(BaseModel):
    """Ground-truth relevance for one query."""

    model_config = ConfigDict(frozen=True)

    query_id: str = Field(min_length=1)
    relevant_ids: frozenset[str]


class QueryEvaluation(BaseModel):
    """The metrics computed for one query at rank ``k``."""

    model_config = ConfigDict(frozen=True)

    query_id: str
    k: int
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float
    ndcg_at_k: float


class EvaluationReport(BaseModel):
    """Aggregate accuracy metrics across an evaluation set."""

    model_config = ConfigDict(frozen=True)

    k: int
    query_count: int
    mean_precision_at_k: float
    mean_recall_at_k: float
    mean_reciprocal_rank: float
    mean_ndcg_at_k: float
    evaluations: tuple[QueryEvaluation, ...] = ()
    meets_thresholds: bool = False


def evaluate_query(
    judgment: QueryJudgment, retrieved: Sequence[str], *, k: int
) -> QueryEvaluation:
    """Compute the ranking metrics for one query."""
    return QueryEvaluation(
        query_id=judgment.query_id,
        k=k,
        precision_at_k=precision_at_k(retrieved, judgment.relevant_ids, k),
        recall_at_k=recall_at_k(retrieved, judgment.relevant_ids, k),
        reciprocal_rank=reciprocal_rank(retrieved, judgment.relevant_ids),
        ndcg_at_k=ndcg_at_k(retrieved, judgment.relevant_ids, k),
    )


def evaluate(
    judgments: Sequence[QueryJudgment],
    results: Mapping[str, Sequence[str]],
    *,
    k: int,
    thresholds: Mapping[str, float] | None = None,
) -> EvaluationReport:
    """Evaluate retrieval results against judgments and optional thresholds."""
    evaluations = tuple(
        evaluate_query(judgment, results.get(judgment.query_id, ()), k=k)
        for judgment in judgments
    )
    count = len(evaluations)
    mean_precision = _mean(e.precision_at_k for e in evaluations)
    mean_recall = _mean(e.recall_at_k for e in evaluations)
    mean_mrr = _mean(e.reciprocal_rank for e in evaluations)
    mean_ndcg = _mean(e.ndcg_at_k for e in evaluations)

    meets = _meets_thresholds(
        thresholds, mean_precision, mean_recall, mean_mrr, mean_ndcg
    )
    return EvaluationReport(
        k=k,
        query_count=count,
        mean_precision_at_k=mean_precision,
        mean_recall_at_k=mean_recall,
        mean_reciprocal_rank=mean_mrr,
        mean_ndcg_at_k=mean_ndcg,
        evaluations=evaluations,
        meets_thresholds=meets,
    )


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 6)


def _meets_thresholds(
    thresholds: Mapping[str, float] | None,
    precision: float,
    recall: float,
    mrr: float,
    ndcg: float,
) -> bool:
    if not thresholds:
        return True
    return (
        precision >= thresholds.get("precision", 0.0)
        and recall >= thresholds.get("recall", 0.0)
        and mrr >= thresholds.get("mrr", 0.0)
        and ndcg >= thresholds.get("ndcg", 0.0)
    )

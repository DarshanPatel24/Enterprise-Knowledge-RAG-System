"""Retrieval accuracy evaluation (handbook Chapter 5 NFRs)."""

from domain.evaluation.harness import (
    EvaluationReport,
    QueryEvaluation,
    QueryJudgment,
    evaluate,
    evaluate_query,
)
from domain.evaluation.metrics import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

__all__ = [
    "EvaluationReport",
    "QueryEvaluation",
    "QueryJudgment",
    "evaluate",
    "evaluate_query",
    "ndcg_at_k",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
]

"""Retrieval accuracy metrics (handbook Chapter 5 NFRs).

Deterministic binary-relevance ranking metrics: Precision@k, Recall@k,
Reciprocal Rank, and NDCG@k. Inputs are the ranked list of retrieved ids and the
set of relevant ids for a query.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def precision_at_k(retrieved: Sequence[str], relevant: frozenset[str], k: int) -> float:
    """Return Precision@k: relevant items in the top ``k`` divided by ``k``."""
    if k <= 0:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for item in top if item in relevant)
    return hits / k


def recall_at_k(retrieved: Sequence[str], relevant: frozenset[str], k: int) -> float:
    """Return Recall@k: relevant items found in the top ``k`` over all relevant."""
    if not relevant:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for item in top if item in relevant)
    return hits / len(relevant)


def reciprocal_rank(retrieved: Sequence[str], relevant: frozenset[str]) -> float:
    """Return the reciprocal rank of the first relevant item (0 if none)."""
    for index, item in enumerate(retrieved):
        if item in relevant:
            return 1.0 / (index + 1)
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], relevant: frozenset[str], k: int) -> float:
    """Return NDCG@k for binary relevance."""
    if k <= 0 or not relevant:
        return 0.0
    dcg = 0.0
    for index, item in enumerate(retrieved[:k]):
        if item in relevant:
            dcg += 1.0 / math.log2(index + 2)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg

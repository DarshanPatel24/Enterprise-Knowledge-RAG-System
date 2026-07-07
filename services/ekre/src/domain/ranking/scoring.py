"""Eligibility filtering and evidence scoring (handbook Chapter 25.7-25.9).

Eligibility removes knowledge objects unsuitable for ranking (empty content, no
evidence). Scoring computes per-factor evidence scores from a knowledge object
and aggregates them into a configurable, versioned composite score. All
computation is deterministic and fully auditable.
"""

from __future__ import annotations

from domain.fusion.models import KnowledgeObject
from domain.query.models import RetrievalEngineType

# Evidence factor -> the retrieval engine that supplies it.
_FACTOR_ENGINE = {
    "semantic": RetrievalEngineType.VECTOR,
    "lexical": RetrievalEngineType.KEYWORD,
    "metadata": RetrievalEngineType.METADATA,
}


def is_eligible(obj: KnowledgeObject) -> bool:
    """Return whether a knowledge object is eligible for ranking."""
    return bool(obj.content.strip()) and bool(obj.evidence)


def factor_scores(obj: KnowledgeObject, *, max_fusion: float) -> dict[str, float]:
    """Compute per-factor evidence scores for a knowledge object.

    Semantic/lexical/metadata factors take the strongest evidence of that engine;
    the fusion factor is the object's RRF score normalized across the set.
    """
    scores: dict[str, float] = {}
    for factor, engine in _FACTOR_ENGINE.items():
        engine_scores = [e.score for e in obj.evidence if e.engine is engine]
        scores[factor] = max(engine_scores) if engine_scores else 0.0
    scores["fusion"] = obj.fusion_score / max_fusion if max_fusion > 0.0 else 0.0
    return scores


def composite_score(factors: dict[str, float], weights: dict[str, float]) -> float:
    """Aggregate factor scores into a weighted composite score."""
    return round(sum(factors.get(name, 0.0) * weight for name, weight in weights.items()), 6)


def build_explanation(
    factors: dict[str, float], weights: dict[str, float], composite: float
) -> str:
    """Render a human-readable ranking explanation for the audit trail."""
    parts = [
        f"{name}={factors.get(name, 0.0):.3f}*{weights[name]:.2f}"
        for name in sorted(weights)
    ]
    return f"composite={composite:.4f} <- " + " + ".join(parts)

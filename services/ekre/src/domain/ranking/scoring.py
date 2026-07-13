"""Eligibility filtering and evidence scoring (handbook Chapter 25.7-25.9).

Eligibility removes knowledge objects unsuitable for ranking (empty content, no
evidence). Scoring computes per-factor evidence scores from a knowledge object
and aggregates them into a configurable, versioned composite score. All
computation is deterministic and fully auditable.
"""

from __future__ import annotations

import re

from domain.fusion.models import KnowledgeObject
from domain.query.models import RetrievalEngineType

# Evidence factor -> the retrieval engine that supplies it.
_FACTOR_ENGINE = {
    "semantic": RetrievalEngineType.VECTOR,
    "lexical": RetrievalEngineType.KEYWORD,
    "metadata": RetrievalEngineType.METADATA,
}

# Word tokenizer for distinctive-term extraction (deterministic).
_TERM = re.compile(r"[A-Za-z0-9]+")

# Generic English function words excluded from distinctive-term coverage so a
# rare, discriminating query term (for example a specific product name) is not
# diluted by common words. This directly addresses similar-named results: a
# document that omits a distinctive term the user typed scores lower coverage
# than one that contains it. The set is extensible and intentionally limited to
# function words so meaningful content terms still count.
_STOP_WORDS = frozenset(
    {
        "a", "about", "an", "and", "any", "are", "as", "at", "be", "been", "by",
        "can", "do", "does", "for", "from", "get", "how", "i", "in", "into", "is",
        "it", "its", "me", "my", "of", "on", "or", "our", "please", "shall",
        "should", "show", "that", "the", "their", "them", "then", "there",
        "these", "they", "this", "to", "us", "was", "we", "were", "what", "when",
        "where", "which", "who", "why", "will", "with", "would", "you", "your",
    }
)


def is_eligible(obj: KnowledgeObject) -> bool:
    """Return whether a knowledge object is eligible for ranking."""
    return bool(obj.content.strip()) and bool(obj.evidence)


def distinctive_terms(query: str) -> frozenset[str]:
    """Return the query's content-bearing terms with function words removed.

    These are the terms coverage scoring treats as discriminating; empty when the
    query carries no content words (coverage then stays neutral).
    """
    return frozenset(
        term
        for term in (match.lower() for match in _TERM.findall(query))
        if len(term) > 1 and term not in _STOP_WORDS
    )


def coverage_score(obj: KnowledgeObject, query_terms: frozenset[str]) -> float:
    """Return the fraction of distinctive query terms present in the object.

    Coverage is measured against the object's identifying text (source path,
    section title, and content) so a document whose title or body names the term
    the user asked for outranks a similarly named document that omits it. Returns
    a neutral ``1.0`` when the query has no distinctive terms.
    """
    if not query_terms:
        return 1.0
    haystack = " ".join(
        (
            obj.citation.source_path,
            obj.citation.section_title or "",
            obj.content,
        )
    ).lower()
    matched = sum(1 for term in query_terms if term in haystack)
    return matched / len(query_terms)


def factor_scores(
    obj: KnowledgeObject,
    *,
    max_fusion: float,
    query_terms: frozenset[str] = frozenset(),
) -> dict[str, float]:
    """Compute per-factor evidence scores for a knowledge object.

    Semantic/lexical/metadata factors take the strongest evidence of that engine;
    the fusion factor is the object's RRF score normalized across the set; the
    coverage factor rewards documents that contain the distinctive query terms.
    """
    scores: dict[str, float] = {}
    for factor, engine in _FACTOR_ENGINE.items():
        engine_scores = [e.score for e in obj.evidence if e.engine is engine]
        scores[factor] = max(engine_scores) if engine_scores else 0.0
    scores["fusion"] = obj.fusion_score / max_fusion if max_fusion > 0.0 else 0.0
    scores["coverage"] = coverage_score(obj, query_terms)
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

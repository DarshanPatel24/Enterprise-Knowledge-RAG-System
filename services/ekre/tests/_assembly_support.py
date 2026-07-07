"""Shared builders for the assembly test suite (not collected)."""

from __future__ import annotations

from _ranking_support import knowledge_object

from domain.query.models import RetrievalEngineType
from domain.ranking.models import RankedKnowledgeObject, RankedKnowledgeSet


def ranked_object(
    document_id: str,
    chunk_id: str,
    *,
    content: str,
    composite: float,
    rank: int,
) -> RankedKnowledgeObject:
    """Build a ranked knowledge object for assembly tests."""
    obj = knowledge_object(
        document_id,
        chunk_id,
        [(RetrievalEngineType.VECTOR, composite, 0)],
        fusion_score=composite,
        content=content,
    )
    return RankedKnowledgeObject(
        knowledge_object=obj,
        rank=rank,
        composite_score=composite,
        factor_scores={"semantic": composite},
        factor_weights={"semantic": 1.0},
        explanation=f"composite={composite:.4f}",
        reranked=False,
    )


def ranked_set(*objects: RankedKnowledgeObject) -> RankedKnowledgeSet:
    """Build a ranked knowledge set from ``objects``."""
    return RankedKnowledgeSet(
        ranking_id="rks-test",
        policy_version="v1",
        objects=tuple(objects),
        object_count=len(objects),
        considered_count=len(objects),
        reranked=False,
    )

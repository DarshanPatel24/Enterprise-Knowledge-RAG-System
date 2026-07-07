"""Shared builders for the ranking test suite (not collected)."""

from __future__ import annotations

from collections.abc import Sequence

from contracts.retrieval import Citation
from domain.fusion import (
    EvidenceSource,
    FusedKnowledgeSet,
    FusionPolicy,
    KnowledgeObject,
)
from domain.query.models import RetrievalEngineType


def knowledge_object(
    document_id: str,
    chunk_id: str,
    evidences: Sequence[tuple[RetrievalEngineType, float, int]],
    *,
    fusion_score: float,
    content: str = "content",
) -> KnowledgeObject:
    """Build a knowledge object from (engine, score, rank) evidence tuples."""
    evidence = tuple(
        EvidenceSource(engine=engine, worker_id=f"{engine.value}-w", score=score, rank=rank)
        for engine, score, rank in evidences
    )
    source_engines = tuple(dict.fromkeys(engine for engine, _, _ in evidences))
    best_score = max((score for _, score, _ in evidences), default=0.0)
    return KnowledgeObject(
        knowledge_id=f"ko-{document_id}-{chunk_id}",
        citation=Citation(
            document_id=document_id,
            chunk_id=chunk_id,
            source_path=f"/docs/{document_id}.md",
        ),
        content=content,
        evidence=evidence,
        source_engines=source_engines,
        fusion_score=fusion_score,
        best_score=best_score,
    )


def fused_set(*objects: KnowledgeObject) -> FusedKnowledgeSet:
    """Build a fused knowledge set from ``objects``."""
    return FusedKnowledgeSet(
        fusion_id="fks-test",
        policy=FusionPolicy.CHUNK_IDENTITY,
        objects=tuple(objects),
        object_count=len(objects),
    )

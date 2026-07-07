"""Candidate Fusion Framework (handbook Chapter 24).

Groups candidates that refer to the same knowledge asset (identity resolution),
aggregates their evidence, and combines their ranks with deterministic
Reciprocal Rank Fusion into immutable Knowledge Objects. Fusion never ranks or
discards information; it consolidates complementary evidence and preserves every
provenance source.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from contracts.retrieval import Citation
from domain.fusion.models import (
    CollectedCandidate,
    EvidenceSource,
    FusedKnowledgeSet,
    FusionPolicy,
    KnowledgeObject,
    UnifiedCandidateSet,
)
from domain.query.models import RetrievalEngineType

_ENGINE_ORDER = {
    RetrievalEngineType.VECTOR: 0,
    RetrievalEngineType.KEYWORD: 1,
    RetrievalEngineType.METADATA: 2,
}


class CandidateFusion:
    """Fuses a Unified Candidate Set into a Fused Knowledge Set."""

    def __init__(self, policy: FusionPolicy, *, rrf_k: int = 60) -> None:
        self._policy = policy
        self._rrf_k = rrf_k

    def fuse(self, ucs: UnifiedCandidateSet) -> FusedKnowledgeSet:
        """Group same-asset candidates and fuse them into Knowledge Objects."""
        groups: dict[tuple[str, ...], list[CollectedCandidate]] = {}
        for item in ucs.candidates:
            key = self._identity_key(item)
            groups.setdefault(key, []).append(item)

        objects = [self._build_object(key, members) for key, members in groups.items()]
        objects.sort(
            key=lambda obj: (
                -obj.fusion_score,
                -obj.best_score,
                obj.citation.document_id,
                obj.citation.chunk_id,
            )
        )
        return FusedKnowledgeSet(
            fusion_id=f"fks-{uuid.uuid4().hex[:12]}",
            policy=self._policy,
            objects=tuple(objects),
            object_count=len(objects),
            warnings=ucs.warnings,
        )

    def _identity_key(self, item: CollectedCandidate) -> tuple[str, ...]:
        citation = item.candidate.citation
        if self._policy is FusionPolicy.DOCUMENT_IDENTITY:
            return (citation.document_id,)
        if self._policy is FusionPolicy.STRICT_IDENTITY:
            return (citation.document_id, citation.chunk_id, citation.source_path)
        return (citation.document_id, citation.chunk_id)

    def _build_object(
        self, key: tuple[str, ...], members: Sequence[CollectedCandidate]
    ) -> KnowledgeObject:
        representative = max(
            members, key=lambda m: (m.score, -_ENGINE_ORDER.get(m.engine, 99))
        )
        ordered = sorted(members, key=lambda m: (_ENGINE_ORDER.get(m.engine, 99), m.rank))
        evidence = tuple(
            EvidenceSource(
                engine=m.engine, worker_id=m.worker_id, score=m.score, rank=m.rank
            )
            for m in ordered
        )
        fusion_score = sum(1.0 / (self._rrf_k + m.rank + 1) for m in members)
        best_score = max(m.score for m in members)
        source_engines = tuple(dict.fromkeys(m.engine for m in ordered))
        citation = representative.candidate.citation
        if self._policy is FusionPolicy.DOCUMENT_IDENTITY:
            citation = Citation(
                document_id=citation.document_id,
                chunk_id=representative.candidate.citation.chunk_id,
                source_path=citation.source_path,
            )
        return KnowledgeObject(
            knowledge_id="ko-" + "-".join(key),
            citation=citation,
            content=representative.candidate.content,
            evidence=evidence,
            source_engines=source_engines,
            fusion_score=fusion_score,
            best_score=best_score,
        )

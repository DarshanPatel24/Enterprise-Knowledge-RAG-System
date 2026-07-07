"""Collection and fusion models (handbook Chapters 23-24).

Retrieval candidates from independent workers are collected into an immutable
Unified Candidate Set, then fused into a Fused Knowledge Set of Knowledge
Objects --- one per knowledge asset --- with all provenance and evidence
preserved. Neither stage ranks or discards information.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from contracts.retrieval import Citation, RetrievalCandidate
from domain.query.models import RetrievalEngineType


class FusionPolicy(StrEnum):
    """Identity resolution policy used to group candidates (handbook 24.13)."""

    CHUNK_IDENTITY = "chunk"
    DOCUMENT_IDENTITY = "document"
    STRICT_IDENTITY = "strict"


class CollectedCandidate(BaseModel):
    """A retrieval candidate annotated with its collection provenance."""

    model_config = ConfigDict(frozen=True)

    candidate: RetrievalCandidate
    worker_id: str
    engine: RetrievalEngineType
    rank: int = Field(ge=0)
    score: float = Field(ge=0.0, le=1.0)


class UnifiedCandidateSet(BaseModel):
    """The canonical, immutable collection of retrieval candidates (UCS)."""

    model_config = ConfigDict(frozen=True)

    collection_id: str = Field(min_length=1)
    candidates: tuple[CollectedCandidate, ...] = ()
    source_counts: dict[str, int] = Field(default_factory=dict)
    total: int = 0
    warnings: tuple[str, ...] = ()


class EvidenceSource(BaseModel):
    """One independently traceable retrieval evidence for a knowledge object."""

    model_config = ConfigDict(frozen=True)

    engine: RetrievalEngineType
    worker_id: str
    score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=0)


class KnowledgeObject(BaseModel):
    """An immutable knowledge asset fused from one or more candidates (24.11)."""

    model_config = ConfigDict(frozen=True)

    knowledge_id: str = Field(min_length=1)
    citation: Citation
    content: str
    evidence: tuple[EvidenceSource, ...]
    source_engines: tuple[RetrievalEngineType, ...]
    fusion_score: float = Field(ge=0.0)
    best_score: float = Field(ge=0.0, le=1.0)


class FusedKnowledgeSet(BaseModel):
    """The fused output: one knowledge object per asset (FKS)."""

    model_config = ConfigDict(frozen=True)

    fusion_id: str = Field(min_length=1)
    policy: FusionPolicy
    objects: tuple[KnowledgeObject, ...] = ()
    object_count: int = 0
    warnings: tuple[str, ...] = ()

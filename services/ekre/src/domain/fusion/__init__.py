"""Candidate collection and fusion (handbook Chapters 23-24)."""

from domain.fusion.collection import CandidateCollector
from domain.fusion.errors import FusionError, FusionErrorType
from domain.fusion.fusion import CandidateFusion
from domain.fusion.models import (
    CollectedCandidate,
    EvidenceSource,
    FusedKnowledgeSet,
    FusionPolicy,
    KnowledgeObject,
    UnifiedCandidateSet,
)

__all__ = [
    "CandidateCollector",
    "CandidateFusion",
    "CollectedCandidate",
    "EvidenceSource",
    "FusedKnowledgeSet",
    "FusionError",
    "FusionErrorType",
    "FusionPolicy",
    "KnowledgeObject",
    "UnifiedCandidateSet",
]

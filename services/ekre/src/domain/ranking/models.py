"""Ranking engine models (handbook Chapter 25).

The Ranking Engine consumes a Fused Knowledge Set and produces a Ranked
Knowledge Set: knowledge objects in relevance order, each carrying the full
audit trail (per-factor evidence scores, weights, composite score, policy
version, rerank flag) so every ranking decision is explainable.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.fusion.models import KnowledgeObject


class RankedKnowledgeObject(BaseModel):
    """A knowledge object with its final rank and ranking audit fields."""

    model_config = ConfigDict(frozen=True)

    knowledge_object: KnowledgeObject
    rank: int = Field(ge=1)
    composite_score: float = Field(ge=0.0)
    factor_scores: dict[str, float] = Field(default_factory=dict)
    factor_weights: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""
    reranked: bool = False


class RankedKnowledgeSet(BaseModel):
    """The ordered ranking output handed to context assembly (RKS)."""

    model_config = ConfigDict(frozen=True)

    ranking_id: str = Field(min_length=1)
    policy_version: str
    objects: tuple[RankedKnowledgeObject, ...] = ()
    object_count: int = 0
    considered_count: int = 0
    reranked: bool = False
    warnings: tuple[str, ...] = ()

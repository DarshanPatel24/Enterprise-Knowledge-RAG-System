"""Memory framework policy resolved from settings.

Encodes the per-scope retention (TTL) rules and the retrieval ranking weights so
no retention period or ranking weight is hardcoded in engine logic. A TTL of 0
means no expiry (indefinite retention), used for organizational memory.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from domain.memory.models import MemoryScope


class MemorySettingsLike(Protocol):
    """Structural view of the memory settings the policy depends on."""

    working_ttl_seconds: float
    session_ttl_seconds: float
    conversation_ttl_seconds: float
    workspace_ttl_seconds: float
    user_ttl_seconds: float
    organizational_ttl_seconds: float
    default_min_confidence: float
    default_classification: str
    max_retrieval_limit: int
    weight_relevance: float
    weight_recency: float
    weight_importance: float
    weight_frequency: float
    weight_trust: float
    recency_half_life_hours: float


class MemoryPolicy(BaseModel):
    """Immutable memory policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    working_ttl_seconds: float = Field(default=1800.0, ge=0.0)
    session_ttl_seconds: float = Field(default=28800.0, ge=0.0)
    conversation_ttl_seconds: float = Field(default=2592000.0, ge=0.0)
    workspace_ttl_seconds: float = Field(default=31536000.0, ge=0.0)
    user_ttl_seconds: float = Field(default=94608000.0, ge=0.0)
    organizational_ttl_seconds: float = Field(default=0.0, ge=0.0)
    default_min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    default_classification: str = "internal"
    max_retrieval_limit: int = Field(default=10, gt=0)
    weight_relevance: float = Field(default=0.4, ge=0.0)
    weight_recency: float = Field(default=0.2, ge=0.0)
    weight_importance: float = Field(default=0.15, ge=0.0)
    weight_frequency: float = Field(default=0.1, ge=0.0)
    weight_trust: float = Field(default=0.15, ge=0.0)
    recency_half_life_hours: float = Field(default=24.0, gt=0.0)

    @classmethod
    def from_settings(cls, settings: MemorySettingsLike) -> MemoryPolicy:
        """Build the memory policy from the memory settings."""
        return cls(
            working_ttl_seconds=settings.working_ttl_seconds,
            session_ttl_seconds=settings.session_ttl_seconds,
            conversation_ttl_seconds=settings.conversation_ttl_seconds,
            workspace_ttl_seconds=settings.workspace_ttl_seconds,
            user_ttl_seconds=settings.user_ttl_seconds,
            organizational_ttl_seconds=settings.organizational_ttl_seconds,
            default_min_confidence=settings.default_min_confidence,
            default_classification=settings.default_classification,
            max_retrieval_limit=settings.max_retrieval_limit,
            weight_relevance=settings.weight_relevance,
            weight_recency=settings.weight_recency,
            weight_importance=settings.weight_importance,
            weight_frequency=settings.weight_frequency,
            weight_trust=settings.weight_trust,
            recency_half_life_hours=settings.recency_half_life_hours,
        )

    def scope_ttl_seconds(self, scope: MemoryScope) -> float | None:
        """Return the TTL for a scope in seconds, or None for indefinite retention."""
        ttl = {
            MemoryScope.WORKING: self.working_ttl_seconds,
            MemoryScope.SESSION: self.session_ttl_seconds,
            MemoryScope.CONVERSATION: self.conversation_ttl_seconds,
            MemoryScope.WORKSPACE: self.workspace_ttl_seconds,
            MemoryScope.USER: self.user_ttl_seconds,
            MemoryScope.ORGANIZATIONAL: self.organizational_ttl_seconds,
        }[scope]
        return None if ttl <= 0.0 else ttl

    def retrieval_weights(self) -> dict[str, float]:
        """Return the retrieval ranking weights keyed by dimension."""
        return {
            "relevance": self.weight_relevance,
            "recency": self.weight_recency,
            "importance": self.weight_importance,
            "frequency": self.weight_frequency,
            "trust": self.weight_trust,
        }

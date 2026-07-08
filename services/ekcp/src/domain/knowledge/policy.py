"""Knowledge policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeSettingsLike(Protocol):
    """Structural view of the knowledge settings the policy depends on."""

    enabled: bool
    base_url: str
    timeout_seconds: float
    max_retries: int
    circuit_breaker_threshold: int
    circuit_breaker_reset_seconds: float
    retrieval_mode: str
    max_candidates: int
    relevance_threshold: float


class KnowledgePolicy(BaseModel):
    """Immutable knowledge integration policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    base_url: str = "http://localhost:8002"
    timeout_seconds: float = Field(default=10.0, gt=0.0)
    max_retries: int = Field(default=3, ge=0)
    circuit_breaker_threshold: int = Field(default=5, gt=0)
    circuit_breaker_reset_seconds: float = Field(default=60.0, gt=0.0)
    retrieval_mode: str = "hybrid"
    max_candidates: int = Field(default=10, gt=0)
    relevance_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    @classmethod
    def from_settings(cls, settings: KnowledgeSettingsLike) -> KnowledgePolicy:
        """Build the knowledge policy from the knowledge settings."""
        return cls(
            enabled=settings.enabled,
            base_url=settings.base_url,
            timeout_seconds=settings.timeout_seconds,
            max_retries=settings.max_retries,
            circuit_breaker_threshold=settings.circuit_breaker_threshold,
            circuit_breaker_reset_seconds=settings.circuit_breaker_reset_seconds,
            retrieval_mode=settings.retrieval_mode,
            max_candidates=settings.max_candidates,
            relevance_threshold=settings.relevance_threshold,
        )

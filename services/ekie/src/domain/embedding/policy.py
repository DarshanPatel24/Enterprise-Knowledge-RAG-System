"""Embedding policy: configuration-driven model selection and limits (handbook 10.9)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from domain.embedding.models import DistanceMetric


class EmbeddingSettingsLike(Protocol):
    """Structural type for environment-backed embedding settings."""

    default_model: str
    provider: str
    dimension: int
    distance_metric: str
    max_input_tokens: int
    batch_size: int
    normalize_vectors: bool
    cost_per_1k_tokens: float
    max_retries: int
    max_requests_per_minute: int


class EmbeddingPolicy(BaseModel):
    """Versioned, configuration-driven embedding behavior (ADR-024)."""

    model_config = {"frozen": True}

    default_model: str = "local-hash-256"
    provider: str = "local"
    dimension: int = Field(default=256, gt=0)
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    max_input_tokens: int = Field(default=8192, gt=0)
    batch_size: int = Field(default=16, gt=0)
    normalize_vectors: bool = True
    cost_per_1k_tokens: float = Field(default=0.0, ge=0.0)
    max_retries: int = Field(default=3, ge=0)
    max_requests_per_minute: int = Field(default=0, ge=0)

    @classmethod
    def from_settings(cls, settings: EmbeddingSettingsLike) -> EmbeddingPolicy:
        """Build a policy from environment-backed embedding settings."""
        return cls(
            default_model=settings.default_model,
            provider=settings.provider,
            dimension=settings.dimension,
            distance_metric=DistanceMetric(settings.distance_metric),
            max_input_tokens=settings.max_input_tokens,
            batch_size=settings.batch_size,
            normalize_vectors=settings.normalize_vectors,
            cost_per_1k_tokens=settings.cost_per_1k_tokens,
            max_retries=settings.max_retries,
            max_requests_per_minute=settings.max_requests_per_minute,
        )

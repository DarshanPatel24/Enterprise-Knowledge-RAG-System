"""Ranking policy built from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class RankingSettingsLike(Protocol):
    """Structural view of the ranking settings the policy needs."""

    candidate_limit: int
    min_composite_score: float
    policy_version: str

    def weights(self) -> dict[str, float]: ...


class RankingPolicy(BaseModel):
    """Configuration-driven ranking policy."""

    model_config = ConfigDict(frozen=True)

    candidate_limit: int = Field(gt=0)
    min_composite_score: float = Field(ge=0.0)
    weights: dict[str, float]
    policy_version: str = "v1"

    @classmethod
    def from_settings(cls, settings: RankingSettingsLike) -> RankingPolicy:
        """Build the ranking policy from the ranking settings."""
        return cls(
            candidate_limit=settings.candidate_limit,
            min_composite_score=settings.min_composite_score,
            weights=settings.weights(),
            policy_version=settings.policy_version,
        )

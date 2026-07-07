"""Ranking policy built from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class RankingSettingsLike(Protocol):
    """Structural view of the ranking settings the policy needs."""

    candidate_limit: int
    min_composite_score: float
    policy_version: str
    enable_llm_reranker: bool
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_temperature: float
    llm_request_timeout_seconds: float

    def weights(self) -> dict[str, float]: ...


class RankingPolicy(BaseModel):
    """Configuration-driven ranking policy."""

    model_config = ConfigDict(frozen=True)

    candidate_limit: int = Field(gt=0)
    min_composite_score: float = Field(ge=0.0)
    weights: dict[str, float]
    policy_version: str = "v1"
    enable_llm_reranker: bool = False
    llm_provider: str = "huggingface"
    llm_model: str = ""
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.0
    llm_request_timeout_seconds: float = 60.0

    @classmethod
    def from_settings(cls, settings: RankingSettingsLike) -> RankingPolicy:
        """Build the ranking policy from the ranking settings."""
        return cls(
            candidate_limit=settings.candidate_limit,
            min_composite_score=settings.min_composite_score,
            weights=settings.weights(),
            policy_version=settings.policy_version,
            enable_llm_reranker=settings.enable_llm_reranker,
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            llm_base_url=settings.llm_base_url,
            llm_temperature=settings.llm_temperature,
            llm_request_timeout_seconds=settings.llm_request_timeout_seconds,
        )

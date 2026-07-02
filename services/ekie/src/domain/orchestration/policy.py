"""Orchestration policy: configuration-driven workflow behavior (handbook 6.20)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from domain.sync.retry import RetryPolicy


class OrchestrationSettingsLike(Protocol):
    """Structural type for environment-backed orchestration settings."""

    runner: str
    max_attempts_per_stage: int
    retry_backoff_base_seconds: float
    retry_backoff_multiplier: float
    enable_tracing: bool


class OrchestrationPolicy(BaseModel):
    """Versioned, configuration-driven orchestration behavior (ADR-020)."""

    model_config = {"frozen": True}

    runner: str = "sequential"
    max_attempts_per_stage: int = Field(default=3, ge=1)
    retry_backoff_base_seconds: float = Field(default=0.0, ge=0.0)
    retry_backoff_multiplier: float = Field(default=2.0, ge=1.0)
    enable_tracing: bool = False

    @classmethod
    def from_settings(cls, settings: OrchestrationSettingsLike) -> OrchestrationPolicy:
        """Build a policy from environment-backed orchestration settings."""
        return cls(
            runner=settings.runner,
            max_attempts_per_stage=settings.max_attempts_per_stage,
            retry_backoff_base_seconds=settings.retry_backoff_base_seconds,
            retry_backoff_multiplier=settings.retry_backoff_multiplier,
            enable_tracing=settings.enable_tracing,
        )

    def retry_policy(self) -> RetryPolicy:
        """Translate the policy into a per-stage retry configuration."""
        return RetryPolicy(
            max_attempts=self.max_attempts_per_stage,
            backoff_base_seconds=self.retry_backoff_base_seconds,
            backoff_multiplier=self.retry_backoff_multiplier,
        )

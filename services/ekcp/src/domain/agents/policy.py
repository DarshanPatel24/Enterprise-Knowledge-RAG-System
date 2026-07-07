"""Agent runtime policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class AgentSettingsLike(Protocol):
    """Structural view of the agent settings the policy depends on."""

    runner: str
    max_steps: int
    base_confidence: float


class AgentPolicy(BaseModel):
    """Immutable agent runtime policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    runner: str = "sequential"
    max_steps: int = Field(default=4, gt=0)
    base_confidence: float = Field(default=0.85, ge=0.0, le=1.0)

    @classmethod
    def from_settings(cls, settings: AgentSettingsLike) -> AgentPolicy:
        """Build the agent policy from the agent settings."""
        return cls(
            runner=settings.runner,
            max_steps=settings.max_steps,
            base_confidence=settings.base_confidence,
        )

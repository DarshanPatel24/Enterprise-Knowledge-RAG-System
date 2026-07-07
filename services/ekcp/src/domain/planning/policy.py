"""Planning policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class PlanningSettingsLike(Protocol):
    """Structural view of the planning settings the policy depends on."""

    max_tasks: int
    default_task_timeout_seconds: float


class PlanningPolicy(BaseModel):
    """Immutable planning policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    max_tasks: int = Field(default=12, gt=0)
    default_task_timeout_seconds: float = Field(default=60.0, gt=0.0)

    @classmethod
    def from_settings(cls, settings: PlanningSettingsLike) -> PlanningPolicy:
        """Build the planning policy from the planning settings."""
        return cls(
            max_tasks=settings.max_tasks,
            default_task_timeout_seconds=settings.default_task_timeout_seconds,
        )

"""Execution policy built from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class ExecutionSettingsLike(Protocol):
    """Structural view of the execution settings the policy needs."""

    runner: str
    max_parallel_workers: int
    default_task_timeout_ms: float
    max_attempts_per_task: int
    admission_enabled: bool
    fail_open: bool
    enable_tracing: bool


class ExecutionPolicy(BaseModel):
    """Configuration-driven policy for the retrieval execution core."""

    model_config = ConfigDict(frozen=True)

    runner: str = "concurrent"
    max_parallel_workers: int = Field(default=4, gt=0)
    default_task_timeout_ms: float = Field(default=150.0, gt=0.0)
    max_attempts_per_task: int = Field(default=1, gt=0)
    admission_enabled: bool = True
    fail_open: bool = True
    enable_tracing: bool = False

    @classmethod
    def from_settings(cls, settings: ExecutionSettingsLike) -> ExecutionPolicy:
        """Build the policy from the execution settings."""
        return cls(
            runner=settings.runner,
            max_parallel_workers=settings.max_parallel_workers,
            default_task_timeout_ms=settings.default_task_timeout_ms,
            max_attempts_per_task=settings.max_attempts_per_task,
            admission_enabled=settings.admission_enabled,
            fail_open=settings.fail_open,
            enable_tracing=settings.enable_tracing,
        )

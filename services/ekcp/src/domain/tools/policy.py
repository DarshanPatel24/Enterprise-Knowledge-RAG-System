"""Tool policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class ToolSettingsLike(Protocol):
    """Structural view of the tool settings the policy depends on."""

    default_timeout_seconds: float
    max_attempts: int
    enforce_permissions: bool


class ToolPolicy(BaseModel):
    """Immutable tool execution policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    default_timeout_seconds: float = Field(default=10.0, gt=0.0)
    max_attempts: int = Field(default=2, ge=1)
    enforce_permissions: bool = True

    @classmethod
    def from_settings(cls, settings: ToolSettingsLike) -> ToolPolicy:
        """Build the tool policy from the tool settings."""
        return cls(
            default_timeout_seconds=settings.default_timeout_seconds,
            max_attempts=settings.max_attempts,
            enforce_permissions=settings.enforce_permissions,
        )

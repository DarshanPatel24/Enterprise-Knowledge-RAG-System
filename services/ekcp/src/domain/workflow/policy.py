"""Workflow policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict


class WorkflowSettingsLike(Protocol):
    """Structural view of the workflow settings the policy depends on."""

    enable_events: bool
    event_bus: str
    source_service: str


class WorkflowPolicy(BaseModel):
    """Immutable workflow policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    enable_events: bool = True
    event_bus: str = "memory"
    source_service: str = "ekcp"

    @classmethod
    def from_settings(cls, settings: WorkflowSettingsLike) -> WorkflowPolicy:
        """Build the workflow policy from the workflow settings."""
        return cls(
            enable_events=settings.enable_events,
            event_bus=settings.event_bus,
            source_service=settings.source_service,
        )

"""Conversation policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict


class ConversationSettingsLike(Protocol):
    """Structural view of the conversation settings the policy depends on."""

    default_workspace_id: str
    default_language: str
    default_priority: str
    archive_on_complete: bool
    enable_events: bool


class ConversationPolicy(BaseModel):
    """Immutable conversation policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    default_workspace_id: str = "default"
    default_language: str = "en"
    default_priority: str = "normal"
    archive_on_complete: bool = False
    enable_events: bool = True

    @classmethod
    def from_settings(cls, settings: ConversationSettingsLike) -> ConversationPolicy:
        """Build the conversation policy from the conversation settings."""
        return cls(
            default_workspace_id=settings.default_workspace_id,
            default_language=settings.default_language,
            default_priority=settings.default_priority,
            archive_on_complete=settings.archive_on_complete,
            enable_events=settings.enable_events,
        )

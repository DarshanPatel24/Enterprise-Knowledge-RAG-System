"""Prompt orchestration policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class PromptSettingsLike(Protocol):
    """Structural view of the prompt settings the policy depends on."""

    default_template_id: str
    max_prompt_tokens: int
    chars_per_token: int
    assistant_identity: str
    assistant_behavior: str
    default_output_format: str


class PromptPolicy(BaseModel):
    """Immutable prompt orchestration policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    default_template_id: str = "enterprise_chat_v1"
    max_prompt_tokens: int = Field(default=12000, gt=0)
    chars_per_token: int = Field(default=4, gt=0)
    assistant_identity: str = "the enterprise knowledge assistant"
    assistant_behavior: str = "Be accurate, concise, and policy-compliant."
    default_output_format: str = "markdown"

    @classmethod
    def from_settings(cls, settings: PromptSettingsLike) -> PromptPolicy:
        """Build the prompt policy from the prompt settings."""
        return cls(
            default_template_id=settings.default_template_id,
            max_prompt_tokens=settings.max_prompt_tokens,
            chars_per_token=settings.chars_per_token,
            assistant_identity=settings.assistant_identity,
            assistant_behavior=settings.assistant_behavior,
            default_output_format=settings.default_output_format,
        )

"""Context orchestration policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class ContextSettingsLike(Protocol):
    """Structural view of the context settings the policy depends on."""

    max_context_tokens: int
    chars_per_token: int
    min_relevance: float
    dedupe_content: bool
    reserve_ratio: float


class ContextPolicy(BaseModel):
    """Immutable context assembly policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    max_context_tokens: int = Field(default=8000, gt=0)
    chars_per_token: int = Field(default=4, gt=0)
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    dedupe_content: bool = True
    reserve_ratio: float = Field(default=0.1, ge=0.0, lt=1.0)

    @classmethod
    def from_settings(cls, settings: ContextSettingsLike) -> ContextPolicy:
        """Build the context policy from the context settings."""
        return cls(
            max_context_tokens=settings.max_context_tokens,
            chars_per_token=settings.chars_per_token,
            min_relevance=settings.min_relevance,
            dedupe_content=settings.dedupe_content,
            reserve_ratio=settings.reserve_ratio,
        )

    def effective_budget(self) -> int:
        """Return the token budget after reserving headroom for generation."""
        return max(1, int(self.max_context_tokens * (1.0 - self.reserve_ratio)))

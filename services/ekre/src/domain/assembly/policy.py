"""Context assembly policy built from settings."""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


class AssemblySettingsLike(Protocol):
    """Structural view of the assembly settings the policy needs."""

    max_context_tokens: int
    max_objects: int
    ordering: str
    normalize_whitespace: bool
    dedupe_content: bool
    chars_per_token: int
    min_relevance: float


class AssemblyPolicy(BaseModel):
    """Configuration-driven context assembly policy."""

    model_config = ConfigDict(frozen=True)

    max_context_tokens: int = Field(gt=0)
    max_objects: int = Field(gt=0)
    ordering: Literal["rank", "document"] = "rank"
    normalize_whitespace: bool = True
    dedupe_content: bool = True
    chars_per_token: int = Field(gt=0)
    min_relevance: float = Field(ge=0.0, le=1.0)

    @classmethod
    def from_settings(cls, settings: AssemblySettingsLike) -> AssemblyPolicy:
        """Build the assembly policy from the assembly settings."""
        return cls(
            max_context_tokens=settings.max_context_tokens,
            max_objects=settings.max_objects,
            ordering=settings.ordering,  # type: ignore[arg-type]
            normalize_whitespace=settings.normalize_whitespace,
            dedupe_content=settings.dedupe_content,
            chars_per_token=settings.chars_per_token,
            min_relevance=settings.min_relevance,
        )

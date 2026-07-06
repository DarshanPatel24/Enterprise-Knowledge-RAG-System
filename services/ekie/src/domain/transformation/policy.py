"""Transformation policy: configuration-driven, deterministic behavior (handbook 7.16)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class TransformationSettingsLike(Protocol):
    """Structural type for environment-backed transformation settings."""

    normalize_unicode: bool
    collapse_blank_lines: bool
    include_front_matter: bool
    default_language: str


class TransformationPolicy(BaseModel):
    """Versioned, configuration-driven transformation behavior."""

    model_config = {"frozen": True}

    normalize_unicode: bool = True
    collapse_blank_lines: bool = True
    include_front_matter: bool = True
    default_language: str = "en"

    @classmethod
    def from_settings(cls, settings: TransformationSettingsLike) -> TransformationPolicy:
        """Build a policy from environment-backed transformation settings."""
        return cls(
            normalize_unicode=settings.normalize_unicode,
            collapse_blank_lines=settings.collapse_blank_lines,
            include_front_matter=settings.include_front_matter,
            default_language=settings.default_language,
        )

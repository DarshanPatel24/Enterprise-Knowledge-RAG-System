"""Document Intelligence policy: configuration-driven analysis (handbook 8.18)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class IntelligenceSettingsLike(Protocol):
    """Structural type for environment-backed intelligence settings."""

    detect_language: bool
    classify_content: bool
    detect_sensitive_content: bool
    default_language: str
    high_complexity_section_threshold: int


class IntelligencePolicy(BaseModel):
    """Versioned, configuration-driven document intelligence behavior."""

    model_config = {"frozen": True}

    detect_language: bool = True
    classify_content: bool = True
    detect_sensitive_content: bool = True
    default_language: str = "en"
    high_complexity_section_threshold: int = 12

    @classmethod
    def from_settings(cls, settings: IntelligenceSettingsLike) -> IntelligencePolicy:
        """Build a policy from environment-backed intelligence settings."""
        return cls(
            detect_language=settings.detect_language,
            classify_content=settings.classify_content,
            detect_sensitive_content=settings.detect_sensitive_content,
            default_language=settings.default_language,
            high_complexity_section_threshold=settings.high_complexity_section_threshold,
        )

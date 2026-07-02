"""Configuration-driven plugin activation policy (handbook 18.13)."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class PluginSettingsLike(Protocol):
    """Structural type for environment-backed plugin settings."""

    require_signature: bool
    allow_unsigned: bool
    ekie_version: str
    sandbox_timeout_seconds: float

    def parsed_trusted_publishers(self) -> frozenset[str]: ...


class PluginPolicy(BaseModel):
    """Versioned, configuration-driven plugin activation behavior (ADR-053)."""

    model_config = {"frozen": True}

    require_signature: bool = True
    allow_unsigned: bool = False
    ekie_version: str = "1.0.0"
    sandbox_timeout_seconds: float = Field(default=5.0, gt=0.0)
    trusted_publishers: frozenset[str] = frozenset()

    @classmethod
    def from_settings(cls, settings: PluginSettingsLike) -> PluginPolicy:
        """Build a policy from environment-backed plugin settings."""
        return cls(
            require_signature=settings.require_signature,
            allow_unsigned=settings.allow_unsigned,
            ekie_version=settings.ekie_version,
            sandbox_timeout_seconds=settings.sandbox_timeout_seconds,
            trusted_publishers=settings.parsed_trusted_publishers(),
        )

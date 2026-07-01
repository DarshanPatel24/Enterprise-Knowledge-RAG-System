"""Synchronization policy (configuration over code).

Policies control which repository objects are synchronized and how change
detection behaves. Defaults are supplied here but every value is overridable
through environment-backed settings, per EKIE handbook Chapter 6.16.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field


class ScanStrategy(StrEnum):
    """Repository scan strategy."""

    FULL = "full"
    INCREMENTAL = "incremental"


class SyncSettingsLike(Protocol):
    """Structural type for the environment-backed sync settings source."""

    scan_strategy: str
    ignore_hidden: bool
    ignore_temp: bool
    max_file_size_bytes: int
    hash_algorithm: str
    rename_detection_enabled: bool
    delete_propagation_enabled: bool
    default_classification: str

    def parsed_extensions(self) -> frozenset[str]:
        """Return the configured allowlist of extensions (empty means all)."""
        ...


class SyncPolicy(BaseModel):
    """Versioned, configuration-driven synchronization behavior."""

    model_config = {"frozen": True}

    scan_strategy: ScanStrategy = ScanStrategy.INCREMENTAL
    ignore_hidden: bool = True
    ignore_temp: bool = True
    max_file_size_bytes: int = Field(default=524_288_000, gt=0)
    allowed_extensions: frozenset[str] = frozenset()
    hash_algorithm: str = "sha256"
    rename_detection_enabled: bool = True
    delete_propagation_enabled: bool = True
    default_classification: str = "internal"

    @classmethod
    def from_settings(cls, settings: SyncSettingsLike) -> SyncPolicy:
        """Build a policy from environment-backed sync settings."""
        return cls(
            scan_strategy=ScanStrategy(settings.scan_strategy),
            ignore_hidden=settings.ignore_hidden,
            ignore_temp=settings.ignore_temp,
            max_file_size_bytes=settings.max_file_size_bytes,
            allowed_extensions=settings.parsed_extensions(),
            hash_algorithm=settings.hash_algorithm,
            rename_detection_enabled=settings.rename_detection_enabled,
            delete_propagation_enabled=settings.delete_propagation_enabled,
            default_classification=settings.default_classification,
        )

    def is_included(self, *, extension: str, size_bytes: int, is_hidden: bool, name: str) -> bool:
        """Return whether an object passes the policy filters."""
        if self.ignore_hidden and is_hidden:
            return False
        if self.ignore_temp and _is_temp_file(name):
            return False
        if self.allowed_extensions and extension.lower() not in self.allowed_extensions:
            return False
        if size_bytes > self.max_file_size_bytes:
            return False
        return True


def _is_temp_file(name: str) -> bool:
    """Return whether ``name`` looks like a temporary or lock file."""
    lowered = name.lower()
    return lowered.startswith("~$") or lowered.endswith((".tmp", "~"))

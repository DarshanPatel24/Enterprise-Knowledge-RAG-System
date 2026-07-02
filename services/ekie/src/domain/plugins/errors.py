"""Plugin SDK error taxonomy (handbook Chapter 18)."""

from __future__ import annotations

from enum import StrEnum


class PluginErrorType(StrEnum):
    """Categories of plugin validation and activation failure."""

    INVALID_MANIFEST = "invalid_manifest"
    INCOMPATIBLE_VERSION = "incompatible_version"
    UNSIGNED = "unsigned"
    UNTRUSTED_PUBLISHER = "untrusted_publisher"
    SANDBOX_FAILURE = "sandbox_failure"
    VALIDATION_FAILED = "validation_failed"
    NOT_ACTIVATED = "not_activated"
    UNKNOWN_PLUGIN = "unknown_plugin"


class PluginError(RuntimeError):
    """Raised when a plugin cannot be validated, activated, or executed."""

    def __init__(self, error_type: PluginErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

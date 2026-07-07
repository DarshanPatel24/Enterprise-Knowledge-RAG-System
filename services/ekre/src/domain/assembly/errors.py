"""Context assembly domain errors."""

from __future__ import annotations

from enum import StrEnum


class AssemblyErrorType(StrEnum):
    """Categories of context assembly failure."""

    CITATION_DROPPED = "citation_dropped"
    INVALID_POLICY = "invalid_policy"


class AssemblyError(Exception):
    """Raised when a ranked knowledge set cannot be assembled into context."""

    def __init__(self, error_type: AssemblyErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

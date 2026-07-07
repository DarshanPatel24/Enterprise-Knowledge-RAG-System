"""Context orchestration domain errors."""

from __future__ import annotations

from enum import StrEnum


class ContextErrorType(StrEnum):
    """Categories of context assembly failure."""

    ASSEMBLY_FAILED = "assembly_failed"
    NOT_FOUND = "not_found"


class ContextError(Exception):
    """Raised when context assembly fails or a context package is missing."""

    def __init__(self, error_type: ContextErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

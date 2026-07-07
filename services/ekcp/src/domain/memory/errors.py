"""Memory framework domain errors."""

from __future__ import annotations

from enum import StrEnum


class MemoryErrorType(StrEnum):
    """Categories of memory framework failure."""

    NOT_FOUND = "not_found"
    INVALID_SCOPE = "invalid_scope"
    NOTHING_TO_CONSOLIDATE = "nothing_to_consolidate"


class MemoryError(Exception):
    """Raised on an invalid memory operation."""

    def __init__(self, error_type: MemoryErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

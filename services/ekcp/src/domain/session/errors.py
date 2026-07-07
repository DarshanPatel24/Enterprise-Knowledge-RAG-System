"""Session domain errors."""

from __future__ import annotations

from enum import StrEnum


class SessionErrorType(StrEnum):
    """Categories of session management failure."""

    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    VERSION_CONFLICT = "version_conflict"
    ALREADY_EXISTS = "already_exists"


class SessionError(Exception):
    """Raised on an invalid session operation."""

    def __init__(self, error_type: SessionErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

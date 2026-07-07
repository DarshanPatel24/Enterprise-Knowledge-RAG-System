"""Intent domain errors."""

from __future__ import annotations

from enum import StrEnum


class IntentErrorType(StrEnum):
    """Categories of intent classification failure."""

    EMPTY_QUERY = "empty_query"
    QUERY_TOO_LONG = "query_too_long"


class IntentError(Exception):
    """Raised when a user message cannot be classified for intent."""

    def __init__(self, error_type: IntentErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

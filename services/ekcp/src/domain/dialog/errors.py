"""Dialog domain errors."""

from __future__ import annotations

from enum import StrEnum


class DialogErrorType(StrEnum):
    """Categories of dialog context failures."""

    EMPTY_MESSAGE = "empty_message"


class DialogError(Exception):
    """Raised for a controlled dialog context failure."""

    def __init__(self, error_type: DialogErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

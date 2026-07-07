"""Conversation domain errors."""

from __future__ import annotations

from enum import StrEnum


class ConversationErrorType(StrEnum):
    """Categories of conversation lifecycle and persistence failure."""

    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    INVALID_TRANSITION = "invalid_transition"
    INVALID_STATE = "invalid_state"
    VERSION_CONFLICT = "version_conflict"
    TENANT_MISMATCH = "tenant_mismatch"
    EMPTY_MESSAGE = "empty_message"


class ConversationError(Exception):
    """Raised on an invalid conversation operation or persistence conflict."""

    def __init__(self, error_type: ConversationErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

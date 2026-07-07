"""Prompt orchestration domain errors."""

from __future__ import annotations

from enum import StrEnum


class PromptErrorType(StrEnum):
    """Categories of prompt construction failure."""

    UNKNOWN_TEMPLATE = "unknown_template"
    MISSING_VARIABLE = "missing_variable"
    POLICY_CONFLICT = "policy_conflict"


class PromptError(Exception):
    """Raised when a prompt cannot be constructed from a template and context."""

    def __init__(self, error_type: PromptErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

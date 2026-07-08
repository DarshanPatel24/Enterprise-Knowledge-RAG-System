"""Workflow orchestration domain errors."""

from __future__ import annotations

from enum import StrEnum


class WorkflowErrorType(StrEnum):
    """Categories of workflow orchestration failure."""

    NOT_FOUND = "not_found"
    INVALID_TRANSITION = "invalid_transition"
    INVALID_STATE = "invalid_state"


class WorkflowError(Exception):
    """Raised on an invalid workflow operation or transition."""

    def __init__(self, error_type: WorkflowErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

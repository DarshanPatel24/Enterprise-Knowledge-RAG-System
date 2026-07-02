"""Orchestration error taxonomy for targeted workflow recovery (handbook 6.20)."""

from __future__ import annotations

from enum import StrEnum


class OrchestrationErrorType(StrEnum):
    """Categories of workflow orchestration failure."""

    MISSING_SOURCE = "missing_source"
    STAGE_FAILURE = "stage_failure"
    DEAD_LETTER = "dead_letter"
    UNKNOWN_STAGE = "unknown_stage"
    RUNNER_UNAVAILABLE = "runner_unavailable"


class OrchestrationError(RuntimeError):
    """Raised when a workflow cannot be orchestrated to completion."""

    def __init__(self, error_type: OrchestrationErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

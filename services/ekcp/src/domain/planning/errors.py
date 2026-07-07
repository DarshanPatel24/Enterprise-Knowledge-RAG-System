"""Planning and orchestration domain errors."""

from __future__ import annotations

from enum import StrEnum


class PlanningErrorType(StrEnum):
    """Categories of planning failure."""

    EMPTY_OBJECTIVE = "empty_objective"
    PLANNING_FAILED = "planning_failed"
    CYCLE_DETECTED = "cycle_detected"


class PlanningError(Exception):
    """Raised when an execution plan cannot be produced."""

    def __init__(self, error_type: PlanningErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

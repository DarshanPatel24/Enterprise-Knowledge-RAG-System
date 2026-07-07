"""Retrieval execution domain errors."""

from __future__ import annotations

from enum import StrEnum


class ExecutionErrorType(StrEnum):
    """Categories of retrieval execution failure."""

    NO_TASKS_ADMITTED = "no_tasks_admitted"
    ALL_WORKERS_FAILED = "all_workers_failed"
    RUNNER_UNAVAILABLE = "runner_unavailable"
    UNKNOWN_WORKER = "unknown_worker"


class ExecutionError(Exception):
    """Raised when a retrieval plan cannot be executed."""

    def __init__(self, error_type: ExecutionErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class WorkerError(Exception):
    """Raised by a worker to signal a controlled, isolable retrieval failure."""

    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

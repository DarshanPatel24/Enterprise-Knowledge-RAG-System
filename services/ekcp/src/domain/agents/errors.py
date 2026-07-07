"""Agent runtime domain errors."""

from __future__ import annotations

from enum import StrEnum


class AgentErrorType(StrEnum):
    """Categories of agent runtime failure."""

    NO_AGENT_FOUND = "no_agent_found"
    UNKNOWN_AGENT = "unknown_agent"
    EXECUTION_FAILED = "execution_failed"
    STEP_LIMIT_EXCEEDED = "step_limit_exceeded"
    RUNNER_UNAVAILABLE = "runner_unavailable"


class AgentError(Exception):
    """Raised when an agent cannot be selected, run, or coordinated."""

    def __init__(self, error_type: AgentErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

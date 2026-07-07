"""Tool execution platform domain errors."""

from __future__ import annotations

from enum import StrEnum


class ToolErrorType(StrEnum):
    """Categories of tool execution failure."""

    UNKNOWN_TOOL = "unknown_tool"
    UNAUTHORIZED = "unauthorized"
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_FAILED = "execution_failed"
    TIMEOUT = "timeout"


class ToolError(Exception):
    """Raised when a tool cannot be discovered, authorized, or executed."""

    def __init__(self, error_type: ToolErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class ToolExecutionFailed(Exception):
    """Controlled, retryable failure raised by a tool adapter."""

    def __init__(self, message: str, *, error_code: str = "tool_error") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code

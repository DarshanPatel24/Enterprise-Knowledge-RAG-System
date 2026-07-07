"""Repository connector framework errors (handbook Chapter 22)."""

from __future__ import annotations

from enum import StrEnum


class ConnectorErrorType(StrEnum):
    """Categories of repository connector failure."""

    CONNECTION_FAILED = "connection_failed"
    SEARCH_FAILED = "search_failed"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"


class ConnectorError(Exception):
    """Raised when a repository connector cannot serve a request."""

    def __init__(self, error_type: ConnectorErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

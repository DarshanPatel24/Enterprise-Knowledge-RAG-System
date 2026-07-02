"""Security and governance error taxonomy (handbook Chapter 17)."""

from __future__ import annotations

from enum import StrEnum


class SecurityErrorType(StrEnum):
    """Categories of security, authorization, and governance failure."""

    UNAUTHENTICATED = "unauthenticated"
    UNAUTHORIZED = "unauthorized"
    CLEARANCE_VIOLATION = "clearance_violation"
    SECRET_UNAVAILABLE = "secret_unavailable"  # noqa: S105 - error code, not a secret
    UNKNOWN_CLASSIFICATION = "unknown_classification"


class SecurityError(RuntimeError):
    """Raised when a security or governance control denies an operation."""

    def __init__(self, error_type: SecurityErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

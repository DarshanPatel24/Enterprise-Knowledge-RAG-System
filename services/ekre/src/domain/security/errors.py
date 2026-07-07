"""Security domain errors for retrieval ingress validation."""

from __future__ import annotations

from enum import StrEnum


class SecurityErrorType(StrEnum):
    """Categories of security context validation failure."""

    MISSING_CONTEXT = "missing_context"
    INVALID_TENANT = "invalid_tenant"
    INVALID_USER = "invalid_user"
    UNKNOWN_CLEARANCE = "unknown_clearance"
    TENANT_MISMATCH = "tenant_mismatch"


class SecurityError(Exception):
    """Raised when a retrieval request carries an invalid security context."""

    def __init__(self, error_type: SecurityErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

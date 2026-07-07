"""Governance, security, and policy domain errors."""

from __future__ import annotations

from enum import StrEnum


class GovernanceErrorType(StrEnum):
    """Categories of governance enforcement failure."""

    UNAUTHORIZED = "unauthorized"
    CLEARANCE_VIOLATION = "clearance_violation"
    POLICY_DENIED = "policy_denied"
    UNKNOWN_CLASSIFICATION = "unknown_classification"


class GovernanceError(Exception):
    """Raised when a governed operation is denied by policy."""

    def __init__(self, error_type: GovernanceErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

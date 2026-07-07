"""Candidate collection and fusion domain errors."""

from __future__ import annotations

from enum import StrEnum


class FusionErrorType(StrEnum):
    """Categories of collection/fusion failure."""

    INVALID_CANDIDATE = "invalid_candidate"
    UNKNOWN_POLICY = "unknown_policy"


class FusionError(Exception):
    """Raised when candidates cannot be collected or fused."""

    def __init__(self, error_type: FusionErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

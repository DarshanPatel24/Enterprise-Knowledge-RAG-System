"""Validation error taxonomy (handbook Chapter 20)."""

from __future__ import annotations

from enum import StrEnum


class ValidationErrorType(StrEnum):
    """Categories of validation and readiness failure."""

    MISSING_ASSET = "missing_asset"
    CORRUPT_ASSET = "corrupt_asset"
    NOT_PUBLISHED = "not_published"


class ValidationError(RuntimeError):
    """Raised when a validation prerequisite cannot be satisfied."""

    def __init__(self, error_type: ValidationErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

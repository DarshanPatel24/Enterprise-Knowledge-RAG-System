"""Transformation error taxonomy for targeted recovery (handbook 7.18)."""

from __future__ import annotations

from enum import StrEnum


class TransformationErrorType(StrEnum):
    """Categories of transformation failure that drive recovery routing."""

    UNSUPPORTED_FORMAT = "unsupported_format"
    PARSER_FAILURE = "parser_failure"
    OCR_FAILURE = "ocr_failure"
    VALIDATION_FAILURE = "validation_failure"
    STORAGE_FAILURE = "storage_failure"
    NOT_FOUND = "not_found"


class TransformationError(RuntimeError):
    """Raised when a document cannot be transformed to a validated asset."""

    def __init__(self, error_type: TransformationErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

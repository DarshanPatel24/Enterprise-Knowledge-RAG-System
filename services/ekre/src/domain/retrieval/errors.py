"""Retrieval worker domain errors."""

from __future__ import annotations

from enum import StrEnum


class RetrievalWorkerErrorType(StrEnum):
    """Categories of retrieval worker failure."""

    UNAUTHORIZED = "unauthorized"
    EMBEDDING_FAILED = "embedding_failed"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"


class RetrievalWorkerError(Exception):
    """Raised for a controlled retrieval worker failure (isolated upstream)."""

    def __init__(self, error_type: RetrievalWorkerErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

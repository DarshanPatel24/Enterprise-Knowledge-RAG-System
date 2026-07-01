"""Embedding error taxonomy for targeted workflow recovery (handbook 10.19)."""

from __future__ import annotations

from enum import StrEnum


class EmbeddingErrorType(StrEnum):
    """Categories of embedding failure."""

    NOT_FOUND = "not_found"
    MISSING_CHUNKS = "missing_chunks"
    UNSUPPORTED_MODEL = "unsupported_model"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"  # noqa: S105 - token budget label, not a secret
    PROVIDER_FAILURE = "provider_failure"
    VALIDATION_FAILURE = "validation_failure"
    STORAGE_FAILURE = "storage_failure"
    EMPTY_RESULT = "empty_result"


class EmbeddingError(RuntimeError):
    """Raised when a document cannot be embedded into an embedding asset."""

    def __init__(self, error_type: EmbeddingErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

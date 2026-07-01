"""Chunking error taxonomy for targeted workflow recovery (handbook 9.18)."""

from __future__ import annotations

from enum import StrEnum


class ChunkingErrorType(StrEnum):
    """Categories of chunking failure."""

    NOT_FOUND = "not_found"
    MISSING_INTELLIGENCE = "missing_intelligence"
    MISSING_MARKDOWN = "missing_markdown"
    EMPTY_RESULT = "empty_result"
    VALIDATION_FAILURE = "validation_failure"
    STORAGE_FAILURE = "storage_failure"


class ChunkingError(RuntimeError):
    """Raised when a document cannot be chunked into a chunk asset."""

    def __init__(self, error_type: ChunkingErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

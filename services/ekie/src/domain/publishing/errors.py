"""Publishing error taxonomy for targeted workflow recovery (handbook 11.19)."""

from __future__ import annotations

from enum import StrEnum


class PublishErrorType(StrEnum):
    """Categories of vector publishing failure."""

    NOT_FOUND = "not_found"
    MISSING_EMBEDDING = "missing_embedding"
    MISSING_CHUNKS = "missing_chunks"
    UNSUPPORTED_PROVIDER = "unsupported_provider"
    COLLECTION_UNAVAILABLE = "collection_unavailable"
    REQUIRED_FIELD_MISSING = "required_field_missing"
    PROVIDER_FAILURE = "provider_failure"
    VERIFICATION_FAILURE = "verification_failure"
    STORAGE_FAILURE = "storage_failure"
    EMPTY_RESULT = "empty_result"


class PublishError(RuntimeError):
    """Raised when a document's vectors cannot be published or verified."""

    def __init__(self, error_type: PublishErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type

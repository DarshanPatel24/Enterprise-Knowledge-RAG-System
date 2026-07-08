"""Knowledge integration domain errors."""

from __future__ import annotations

from enum import StrEnum


class KnowledgeErrorType(StrEnum):
    """Categories of knowledge retrieval failure."""

    EKRE_UNAVAILABLE = "ekre_unavailable"
    CIRCUIT_OPEN = "circuit_open"
    BACKPRESSURE = "backpressure"
    TIMEOUT = "timeout"
    RETRIEVAL_FAILED = "retrieval_failed"


class KnowledgeError(Exception):
    """Raised when enterprise knowledge cannot be retrieved from EKRE."""

    def __init__(self, error_type: KnowledgeErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

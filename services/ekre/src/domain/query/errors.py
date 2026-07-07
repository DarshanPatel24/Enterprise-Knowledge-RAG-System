"""Query intelligence domain errors."""

from __future__ import annotations

from enum import StrEnum


class QueryIntelligenceErrorType(StrEnum):
    """Categories of query intelligence failure."""

    EMPTY_QUERY = "empty_query"
    QUERY_TOO_LONG = "query_too_long"
    INTERPRETER_UNAVAILABLE = "interpreter_unavailable"
    PLANNING_FAILED = "planning_failed"


class QueryIntelligenceError(Exception):
    """Raised when a query cannot be understood, classified, or planned."""

    def __init__(self, error_type: QueryIntelligenceErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

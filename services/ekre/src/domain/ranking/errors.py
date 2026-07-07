"""Ranking engine domain errors."""

from __future__ import annotations

from enum import StrEnum


class RankingErrorType(StrEnum):
    """Categories of ranking failure."""

    RERANKER_UNAVAILABLE = "reranker_unavailable"
    INVALID_POLICY = "invalid_policy"


class RankingError(Exception):
    """Raised when a fused knowledge set cannot be ranked."""

    def __init__(self, error_type: RankingErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

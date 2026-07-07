"""Inheritance domain errors for embedding and distance metric resolution."""

from __future__ import annotations

from enum import StrEnum


class InheritanceErrorType(StrEnum):
    """Categories of inheritance resolution failure."""

    COLLECTION_UNAVAILABLE = "collection_unavailable"
    METRIC_UNRESOLVED = "metric_unresolved"
    DIMENSION_UNRESOLVED = "dimension_unresolved"
    MODEL_UNRESOLVED = "model_unresolved"


class InheritanceError(Exception):
    """Raised when EKIE embedding or distance settings cannot be inherited."""

    def __init__(self, error_type: InheritanceErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message

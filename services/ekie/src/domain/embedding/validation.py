"""Embedding validation rules (handbook 10.14)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum


class EmbeddingValidationErrorType(StrEnum):
    """Categories of embedding validation failure (handbook 10.14)."""

    WRONG_DIMENSION = "wrong_dimension"
    EMPTY_VECTOR = "empty_vector"
    NON_FINITE_VALUE = "non_finite_value"
    ZERO_VECTOR = "zero_vector"


@dataclass(frozen=True)
class EmbeddingValidationReport:
    """The outcome of validating a single embedding vector."""

    valid: bool
    errors: list[EmbeddingValidationErrorType] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


class EmbeddingValidator:
    """Applies deterministic validation rules to generated vectors."""

    def __init__(self, expected_dimension: int) -> None:
        self._expected_dimension = expected_dimension

    def validate(self, values: list[float]) -> EmbeddingValidationReport:
        """Validate a vector's dimension, finiteness, and non-zero magnitude."""
        errors: list[EmbeddingValidationErrorType] = []
        messages: list[str] = []

        if not values:
            errors.append(EmbeddingValidationErrorType.EMPTY_VECTOR)
            messages.append("embedding vector is empty")
            return EmbeddingValidationReport(valid=False, errors=errors, messages=messages)

        if len(values) != self._expected_dimension:
            errors.append(EmbeddingValidationErrorType.WRONG_DIMENSION)
            messages.append(
                f"vector has {len(values)} dimensions; expected "
                f"{self._expected_dimension}"
            )

        if any(not math.isfinite(value) for value in values):
            errors.append(EmbeddingValidationErrorType.NON_FINITE_VALUE)
            messages.append("vector contains NaN or infinite values")

        if all(value == 0.0 for value in values):
            errors.append(EmbeddingValidationErrorType.ZERO_VECTOR)
            messages.append("vector is a zero vector")

        return EmbeddingValidationReport(
            valid=not errors, errors=errors, messages=messages
        )

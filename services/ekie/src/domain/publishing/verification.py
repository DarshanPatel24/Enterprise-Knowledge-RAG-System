"""Publish verification framework (handbook 11.13, ADR-026).

Publishing is complete only after verification confirms the vector exists in the
provider with the correct dimension, collection, and metadata. Verification
reads each point back and compares it against the expected point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from domain.publishing.models import VectorPoint
from domain.publishing.providers.base import VectorProvider


class VerificationErrorType(StrEnum):
    """Categories of publish verification failure (handbook 11.13)."""

    MISSING_VECTOR = "missing_vector"
    DIMENSION_MISMATCH = "dimension_mismatch"
    METADATA_MISMATCH = "metadata_mismatch"
    COLLECTION_MISMATCH = "collection_mismatch"


@dataclass(frozen=True)
class VerificationReport:
    """The outcome of verifying a set of published vectors."""

    verified: bool
    verified_count: int
    errors: list[VerificationErrorType] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


class PublishVerifier:
    """Reads published vectors back and confirms durable, correct storage."""

    def __init__(self, provider: VectorProvider) -> None:
        self._provider = provider

    def verify(self, collection: str, expected: list[VectorPoint]) -> VerificationReport:
        """Verify every expected point exists with matching schema and metadata."""
        errors: list[VerificationErrorType] = []
        messages: list[str] = []
        verified_count = 0

        for point in expected:
            stored = self._provider.fetch(collection, point.vector_id)
            if stored is None:
                errors.append(VerificationErrorType.MISSING_VECTOR)
                messages.append(f"vector {point.vector_id!r} not found after publish")
                continue
            if len(stored.values) != len(point.values):
                errors.append(VerificationErrorType.DIMENSION_MISMATCH)
                messages.append(
                    f"vector {point.vector_id!r} dimension {len(stored.values)} "
                    f"does not match expected {len(point.values)}"
                )
                continue
            if stored.metadata.collection != collection:
                errors.append(VerificationErrorType.COLLECTION_MISMATCH)
                messages.append(
                    f"vector {point.vector_id!r} stored in collection "
                    f"{stored.metadata.collection!r}, expected {collection!r}"
                )
                continue
            if stored.metadata != point.metadata:
                errors.append(VerificationErrorType.METADATA_MISMATCH)
                messages.append(f"vector {point.vector_id!r} metadata mismatch")
                continue
            verified_count += 1

        return VerificationReport(
            verified=not errors,
            verified_count=verified_count,
            errors=errors,
            messages=messages,
        )

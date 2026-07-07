"""Vector provider abstraction (handbook 11.5, ADR-028).

Vector databases are accessed exclusively through this interface so the vector
technology can be replaced without modifying the publishing framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from domain.publishing.collections import CollectionSpec
from domain.publishing.models import VectorPoint


class VectorProviderError(RuntimeError):
    """Raised when a vector provider operation fails."""


class VectorProvider(ABC):
    """A pluggable vector database provider (handbook 11.5, ADR-028)."""

    name: ClassVar[str]

    @abstractmethod
    def ensure_collection(self, spec: CollectionSpec) -> None:
        """Create the collection if absent, enforcing its schema.

        Implementations must reject a request whose dimension or distance metric
        conflicts with an existing collection of the same name.
        """

    @abstractmethod
    def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        """Insert or replace vectors idempotently by vector identity (ADR-027)."""

    @abstractmethod
    def fetch(self, collection: str, vector_id: str) -> VectorPoint | None:
        """Return the stored point for ``vector_id`` or ``None`` if absent."""

    @abstractmethod
    def delete(self, collection: str, vector_ids: list[str]) -> None:
        """Remove vectors by identity so no orphan vectors remain (handbook 11.15)."""

    @abstractmethod
    def delete_by_document(
        self, collection: str, tenant_id: str, document_id: str
    ) -> int:
        """Delete every vector whose metadata matches ``document_id`` for a tenant.

        Returns the number of vectors removed. Unlike :meth:`delete`, this does
        not require knowing individual vector identities, so orphaned vectors can
        be reclaimed even when the published manifest is unavailable. Providers
        must return ``0`` when the collection or document is absent.
        """

    @abstractmethod
    def count(self, collection: str) -> int:
        """Return the number of vectors currently stored in the collection."""

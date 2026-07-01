"""Local in-memory vector provider (handbook 11.5, local-first).

A deterministic, dependency-free vector store used as the default provider. It
implements the full publishing contract so the framework can be exercised end
to end without an external vector database, honoring the local-first principle.
The same contract is implemented by external providers (for example Qdrant).
"""

from __future__ import annotations

from typing import ClassVar

from domain.publishing.collections import CollectionSpec
from domain.publishing.models import VectorPoint
from domain.publishing.providers.base import VectorProvider, VectorProviderError


class InMemoryVectorProvider(VectorProvider):
    """An in-process vector store with schema enforcement and idempotency."""

    name: ClassVar[str] = "local"

    def __init__(self) -> None:
        self._collections: dict[str, CollectionSpec] = {}
        self._points: dict[str, dict[str, VectorPoint]] = {}

    def ensure_collection(self, spec: CollectionSpec) -> None:
        """Create the collection or validate an existing one's schema."""
        existing = self._collections.get(spec.name)
        if existing is None:
            self._collections[spec.name] = spec
            self._points.setdefault(spec.name, {})
            return
        if (
            existing.dimension != spec.dimension
            or existing.distance_metric != spec.distance_metric
        ):
            raise VectorProviderError(
                f"collection {spec.name!r} schema conflict: "
                f"existing dim={existing.dimension}/{existing.distance_metric}, "
                f"requested dim={spec.dimension}/{spec.distance_metric}"
            )

    def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        """Insert or replace points idempotently by vector identity."""
        store = self._require_collection(collection)
        spec = self._collections[collection]
        for point in points:
            if len(point.values) != spec.dimension:
                raise VectorProviderError(
                    f"point {point.vector_id!r} has {len(point.values)} dimensions; "
                    f"collection {collection!r} requires {spec.dimension}"
                )
            store[point.vector_id] = point

    def fetch(self, collection: str, vector_id: str) -> VectorPoint | None:
        """Return the stored point for ``vector_id`` or ``None``."""
        return self._require_collection(collection).get(vector_id)

    def delete(self, collection: str, vector_ids: list[str]) -> None:
        """Remove the given vectors from the collection."""
        store = self._require_collection(collection)
        for vector_id in vector_ids:
            store.pop(vector_id, None)

    def count(self, collection: str) -> int:
        """Return the number of vectors stored in the collection."""
        return len(self._require_collection(collection))

    def _require_collection(self, collection: str) -> dict[str, VectorPoint]:
        store = self._points.get(collection)
        if store is None:
            raise VectorProviderError(f"collection {collection!r} does not exist")
        return store

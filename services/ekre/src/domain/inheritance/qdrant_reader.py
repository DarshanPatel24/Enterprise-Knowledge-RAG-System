"""Qdrant-backed schema reader for inheriting EKIE embedding settings.

Reads the distance metric and dimension from the live Qdrant collection schema
and the embedding model name from a sample vector payload. All Qdrant imports
are lazy so the deterministic offline path never requires ``qdrant-client``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from contracts.enums import DistanceMetric
from domain.inheritance.errors import InheritanceError, InheritanceErrorType
from domain.inheritance.metadata import CollectionSchema

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

# Qdrant distance enum values mapped back to the shared DistanceMetric contract.
_DISTANCE_FROM_QDRANT = {
    "Cosine": DistanceMetric.COSINE,
    "Dot": DistanceMetric.DOT_PRODUCT,
    "Euclid": DistanceMetric.EUCLIDEAN,
}

# Payload fields carrying the EKIE-published embedding model + version.
_MODEL_FIELD = "embedding_model"
_VERSION_FIELD = "embedding_version"


class QdrantClientFactory(Protocol):
    """Builds a Qdrant client on demand (kept lazy for the offline path)."""

    def __call__(self) -> QdrantClient:
        """Return a connected Qdrant client."""
        ...


class QdrantSchemaReader:
    """Read collection schema and sample payload metadata from Qdrant."""

    def __init__(self, client_factory: QdrantClientFactory) -> None:
        self._client_factory = client_factory

    def read(self, collection: str) -> CollectionSchema:
        """Return the schema for ``collection`` read from live Qdrant."""
        try:
            client = self._client_factory()
            info = client.get_collection(collection)
        except Exception as exc:  # noqa: BLE001 - external client boundary
            raise InheritanceError(
                InheritanceErrorType.COLLECTION_UNAVAILABLE,
                f"could not read Qdrant collection {collection!r}: {exc}",
            ) from exc

        dimension, distance_metric = _read_vector_params(info)
        embedding_model, embedding_version = self._read_payload_metadata(client, collection)

        return CollectionSchema(
            collection=collection,
            dimension=dimension,
            distance_metric=distance_metric,
            embedding_model=embedding_model,
            embedding_version=embedding_version,
        )

    def _read_payload_metadata(
        self, client: QdrantClient, collection: str
    ) -> tuple[str | None, int | None]:
        try:
            points, _ = client.scroll(
                collection_name=collection,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )
        except Exception:  # noqa: BLE001 - payload sampling is best-effort
            return None, None
        if not points:
            return None, None
        payload = points[0].payload or {}
        model = payload.get(_MODEL_FIELD)
        version = payload.get(_VERSION_FIELD)
        model_str = str(model) if model else None
        version_int = int(version) if isinstance(version, int) else None
        return model_str, version_int


def _read_vector_params(info: object) -> tuple[int | None, DistanceMetric | None]:
    """Extract dimension and distance metric from a Qdrant collection info object."""
    vectors = getattr(getattr(info, "config", None), "params", None)
    vectors = getattr(vectors, "vectors", None)
    size = getattr(vectors, "size", None)
    distance = getattr(vectors, "distance", None)
    dimension = int(size) if isinstance(size, int) else None
    metric = _DISTANCE_FROM_QDRANT.get(str(distance)) if distance is not None else None
    return dimension, metric

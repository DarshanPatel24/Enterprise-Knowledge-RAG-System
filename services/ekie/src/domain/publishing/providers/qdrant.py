"""Qdrant-backed vector provider (real vector database, local-first).

Implements the vector publishing contract (ADR-028) against a self-hosted
Qdrant instance so published vectors can be exercised end to end against a real
vector database. Vector identities are deterministic strings (ADR-027); because
Qdrant point identifiers must be UUIDs or unsigned integers, each vector id is
mapped to a deterministic UUID5 and the original id plus full metadata are
retained in the point payload for faithful read-back and verification. The
in-memory provider remains the default so the pipeline stays offline unless this
provider is selected by configuration.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, ClassVar

from domain.publishing.collections import CollectionSpec
from domain.publishing.models import VectorMetadata, VectorPoint
from domain.publishing.providers.base import VectorProvider, VectorProviderError

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

# Fixed namespace so a vector id always maps to the same Qdrant point id.
_VECTOR_ID_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
_DISTANCE_BY_METRIC = {
    "cosine": "Cosine",
    "dot_product": "Dot",
    "euclidean": "Euclid",
}
_DEFAULT_TIMEOUT_SECONDS = 30.0


class QdrantVectorProvider(VectorProvider):
    """Vector provider backed by a self-hosted Qdrant database (handbook 11.5)."""

    name: ClassVar[str] = "qdrant"

    def __init__(
        self,
        *,
        host: str,
        port: int,
        url: str = "",
        api_key: str = "",
        request_timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Configure the Qdrant connection without connecting eagerly."""
        self._host = host
        self._port = port
        self._url = url
        self._api_key = api_key
        self._request_timeout_seconds = request_timeout_seconds
        self._client_instance: QdrantClient | None = None

    def ensure_collection(self, spec: CollectionSpec) -> None:
        """Create the collection or validate an existing one's schema."""
        client = self._client()
        from qdrant_client import models as qmodels

        distance_value = _DISTANCE_BY_METRIC.get(spec.distance_metric)
        if distance_value is None:
            raise VectorProviderError(
                f"unsupported distance metric {spec.distance_metric!r} for qdrant"
            )
        if self._collection_exists(client, spec.name):
            self._verify_schema(client, spec, distance_value)
            return
        try:
            client.create_collection(
                collection_name=spec.name,
                vectors_config=qmodels.VectorParams(
                    size=spec.dimension, distance=qmodels.Distance(distance_value)
                ),
            )
        except Exception as exc:  # qdrant client boundary: normalize to domain error
            raise VectorProviderError(
                f"qdrant create_collection failed for {spec.name!r}: {exc}"
            ) from exc

    def upsert(self, collection: str, points: list[VectorPoint]) -> None:
        """Insert or replace points idempotently by deterministic identity."""
        client = self._client()
        from qdrant_client import models as qmodels

        structs = [
            qmodels.PointStruct(
                id=self._point_id(point.vector_id),
                vector=list(point.values),
                payload={
                    "vector_id": point.vector_id,
                    "metadata": point.metadata.model_dump(mode="json"),
                },
            )
            for point in points
        ]
        try:
            client.upsert(collection_name=collection, points=structs)
        except Exception as exc:  # qdrant client boundary: normalize to domain error
            raise VectorProviderError(
                f"qdrant upsert failed for collection {collection!r}: {exc}"
            ) from exc

    def fetch(self, collection: str, vector_id: str) -> VectorPoint | None:
        """Return the stored point for ``vector_id`` or ``None`` if absent."""
        client = self._client()
        try:
            records = client.retrieve(
                collection_name=collection,
                ids=[self._point_id(vector_id)],
                with_vectors=True,
                with_payload=True,
            )
        except Exception as exc:  # qdrant client boundary: normalize to domain error
            raise VectorProviderError(
                f"qdrant retrieve failed for collection {collection!r}: {exc}"
            ) from exc
        if not records:
            return None
        record = records[0]
        payload = record.payload or {}
        metadata = VectorMetadata.model_validate(payload["metadata"])
        raw_vector = record.vector if isinstance(record.vector, list) else []
        values = [float(value) for value in raw_vector]  # type: ignore[arg-type]
        return VectorPoint(
            vector_id=str(payload.get("vector_id", vector_id)),
            values=values,
            metadata=metadata,
        )

    def delete(self, collection: str, vector_ids: list[str]) -> None:
        """Remove vectors by identity so no orphan vectors remain."""
        client = self._client()
        from qdrant_client import models as qmodels

        selector = qmodels.PointIdsList(
            points=[self._point_id(vector_id) for vector_id in vector_ids]
        )
        try:
            client.delete(collection_name=collection, points_selector=selector)
        except Exception as exc:  # qdrant client boundary: normalize to domain error
            raise VectorProviderError(
                f"qdrant delete failed for collection {collection!r}: {exc}"
            ) from exc

    def count(self, collection: str) -> int:
        """Return the number of vectors currently stored in the collection."""
        client = self._client()
        try:
            result = client.count(collection_name=collection, exact=True)
        except Exception as exc:  # qdrant client boundary: normalize to domain error
            raise VectorProviderError(
                f"qdrant count failed for collection {collection!r}: {exc}"
            ) from exc
        return int(result.count)

    def _client(self) -> QdrantClient:
        client = self._client_instance
        if client is None:
            from domain.integrations.langchain_resources import (
                LangChainResourceError,
                build_qdrant_client,
            )

            try:
                client = build_qdrant_client(
                    host=self._host,
                    port=self._port,
                    url=self._url or None,
                    api_key=self._api_key or None,
                    timeout_seconds=self._request_timeout_seconds,
                )
            except LangChainResourceError as exc:
                raise VectorProviderError(str(exc)) from exc
            self._client_instance = client
        return client

    @staticmethod
    def _collection_exists(client: QdrantClient, name: str) -> bool:
        try:
            return bool(client.collection_exists(name))
        except Exception as exc:  # qdrant client boundary: normalize to domain error
            raise VectorProviderError(
                f"qdrant collection_exists failed for {name!r}: {exc}"
            ) from exc

    @staticmethod
    def _verify_schema(
        client: QdrantClient, spec: CollectionSpec, distance_value: str
    ) -> None:
        try:
            info = client.get_collection(spec.name)
            vectors = info.config.params.vectors
            existing_size = int(vectors.size)  # type: ignore[union-attr]
            existing_distance = str(
                getattr(vectors.distance, "value", vectors.distance)  # type: ignore[union-attr]
            )
        except Exception as exc:  # qdrant client boundary: normalize to domain error
            raise VectorProviderError(
                f"qdrant get_collection failed for {spec.name!r}: {exc}"
            ) from exc
        if existing_size != spec.dimension or existing_distance != distance_value:
            raise VectorProviderError(
                f"collection {spec.name!r} schema conflict: "
                f"existing dim={existing_size}/{existing_distance}, "
                f"requested dim={spec.dimension}/{distance_value}"
            )

    @staticmethod
    def _point_id(vector_id: str) -> str:
        return str(uuid.uuid5(_VECTOR_ID_NAMESPACE, vector_id))

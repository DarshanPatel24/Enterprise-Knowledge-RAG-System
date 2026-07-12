"""Qdrant repository connector (live vector store).

Talks to the shared Qdrant collection published by EKIE through the single
LangChain/Qdrant seam. The clearance filter is pushed into the Qdrant query so
unauthorized documents are never returned by the database. All Qdrant imports
are lazy, so the offline path never requires ``qdrant-client``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from domain.connectors.base import (
    Capability,
    RepositoryConnector,
    RepositoryDocument,
)
from domain.connectors.errors import ConnectorError, ConnectorErrorType
from domain.integrations import LangChainResourceError, build_qdrant_client
from domain.query.models import MetadataFilter

_CLEARANCE_FIELD = "classification_clearance"
_TENANT_FIELD = "tenant_id"


class QdrantRetrievalConnector(RepositoryConnector):
    """Repository connector backed by a live Qdrant collection."""

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 6333,
        url: str = "",
        api_key: str = "",
        timeout_seconds: float = 30.0,
        metadata_key: str = "metadata",
    ) -> None:
        self._host = host
        self._port = port
        self._url = url
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._metadata_key = metadata_key
        self._client: Any = None

    def capabilities(self) -> frozenset[Capability]:
        """Return all three search capabilities."""
        return frozenset(
            {
                Capability.VECTOR_SEARCH,
                Capability.KEYWORD_SEARCH,
                Capability.METADATA_SEARCH,
            }
        )

    def vector_search(
        self,
        collection: str,
        vector: Sequence[float],
        *,
        limit: int,
        allowed_clearances: Sequence[str],
        tenant_id: str = "",
        metadata_filters: Sequence[MetadataFilter] = (),
    ) -> list[RepositoryDocument]:
        """Execute a Qdrant similarity search with a clearance + tenant filter."""
        client = self._connect()
        query_filter = self._build_filter(allowed_clearances, metadata_filters, tenant_id)
        try:
            response = client.query_points(
                collection_name=collection,
                query=list(vector),
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            points = response.points
        except Exception as exc:  # noqa: BLE001 - external client boundary
            raise ConnectorError(
                ConnectorErrorType.SEARCH_FAILED, f"qdrant vector search failed: {exc}"
            ) from exc
        return [
            self._to_document(self._metadata(point.payload or {}), float(point.score))
            for point in points
        ]

    def keyword_search(
        self,
        collection: str,
        terms: Sequence[str],
        *,
        limit: int,
        allowed_clearances: Sequence[str],
        tenant_id: str = "",
        metadata_filters: Sequence[MetadataFilter] = (),
    ) -> list[RepositoryDocument]:
        """Scroll clearance + tenant filtered points and rank by content overlap."""
        wanted = [term.lower() for term in terms if term]
        if not wanted:
            return []
        records = self._scroll(
            collection, allowed_clearances, metadata_filters, limit * 4, tenant_id
        )
        scored: list[tuple[float, RepositoryDocument]] = []
        for metadata in records:
            content = str(metadata.get("content", "")).lower()
            matches = sum(1 for term in wanted if term in content)
            if matches:
                scored.append((matches / len(wanted), self._to_document(metadata, 0.0)))
        scored.sort(
            key=lambda item: (-item[0], item[1].document_id, item[1].chunk_id)
        )
        return [doc.model_copy(update={"score": score}) for score, doc in scored[:limit]]

    def metadata_search(
        self,
        collection: str,
        metadata_filters: Sequence[MetadataFilter],
        *,
        limit: int,
        allowed_clearances: Sequence[str],
        tenant_id: str = "",
    ) -> list[RepositoryDocument]:
        """Scroll points matching the clearance, tenant, and metadata filters."""
        if not metadata_filters:
            return []
        records = self._scroll(
            collection, allowed_clearances, metadata_filters, limit, tenant_id
        )
        return [self._to_document(metadata, 1.0) for metadata in records]

    def _connect(self) -> Any:  # noqa: ANN401 - QdrantClient type is lazy
        if self._client is None:
            try:
                self._client = build_qdrant_client(
                    host=self._host,
                    port=self._port,
                    url=self._url or None,
                    api_key=self._api_key or None,
                    timeout_seconds=self._timeout_seconds,
                )
            except LangChainResourceError as exc:
                raise ConnectorError(
                    ConnectorErrorType.CONNECTION_FAILED, str(exc)
                ) from exc
        return self._client

    def _scroll(
        self,
        collection: str,
        allowed_clearances: Sequence[str],
        metadata_filters: Sequence[MetadataFilter],
        limit: int,
        tenant_id: str = "",
    ) -> list[Mapping[str, Any]]:
        client = self._connect()
        query_filter = self._build_filter(allowed_clearances, metadata_filters, tenant_id)
        try:
            points, _ = client.scroll(
                collection_name=collection,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as exc:  # noqa: BLE001 - external client boundary
            raise ConnectorError(
                ConnectorErrorType.SEARCH_FAILED, f"qdrant scroll failed: {exc}"
            ) from exc
        return [self._metadata(point.payload or {}) for point in points]

    def _metadata(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return the governance metadata dict EKIE nests under the metadata key."""
        if self._metadata_key:
            nested = payload.get(self._metadata_key)
            if isinstance(nested, Mapping):
                return nested
        return payload

    def _field_key(self, field: str) -> str:
        """Return the payload key path for ``field`` under the metadata prefix."""
        return f"{self._metadata_key}.{field}" if self._metadata_key else field

    def _build_filter(
        self,
        allowed_clearances: Sequence[str],
        metadata_filters: Sequence[MetadataFilter],
        tenant_id: str = "",
    ) -> Any:  # noqa: ANN401 - qdrant models are lazy
        from qdrant_client import models

        conditions: list[Any] = [
            models.FieldCondition(
                key=self._field_key(_CLEARANCE_FIELD),
                match=models.MatchAny(any=list(allowed_clearances)),
            )
        ]
        if tenant_id:
            conditions.append(
                models.FieldCondition(
                    key=self._field_key(_TENANT_FIELD),
                    match=models.MatchValue(value=tenant_id),
                )
            )
        for metadata_filter in metadata_filters:
            conditions.append(self._filter_condition(models, metadata_filter))
        return models.Filter(must=conditions)

    def _filter_condition(self, models: Any, metadata_filter: MetadataFilter) -> Any:  # noqa: ANN401
        key = self._field_key(metadata_filter.field)
        if metadata_filter.operator in {"gte", "lte"}:
            try:
                bound = float(metadata_filter.value)
            except ValueError:
                return models.FieldCondition(
                    key=key, match=models.MatchValue(value=metadata_filter.value)
                )
            range_kwargs = {metadata_filter.operator: bound}
            return models.FieldCondition(key=key, range=models.Range(**range_kwargs))
        return models.FieldCondition(
            key=key, match=models.MatchValue(value=metadata_filter.value)
        )

    def _to_document(self, metadata: Mapping[str, Any], score: float) -> RepositoryDocument:
        return RepositoryDocument(
            document_id=str(metadata.get("document_id", "unknown")),
            chunk_id=str(metadata.get("chunk_id", "unknown")),
            content=str(metadata.get("content", "")),
            source_path=str(metadata.get("source_path", "")),
            score=max(0.0, min(1.0, score)),
            tenant_id=str(metadata.get(_TENANT_FIELD, "")),
            classification_clearance=str(metadata.get(_CLEARANCE_FIELD, "public")),
            repository_id=str(metadata.get("repository_id", "")),
            section_id=_optional_str(metadata.get("section_id")),
            section_title=_optional_str(metadata.get("section_title")),
            language=_optional_str(metadata.get("language")),
        )


def _optional_str(value: Any) -> str | None:  # noqa: ANN401
    return str(value) if value else None

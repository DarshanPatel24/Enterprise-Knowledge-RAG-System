"""Dynamic inheritance of embedding and distance settings from EKIE metadata.

EKRE must query the same Qdrant collection with the same embedding model and
distance metric that EKIE used to publish the stored vectors. Nothing here is
hardcoded: the distance metric and dimension are read from the live Qdrant
collection schema, and the embedding model name is read from the vector payload
metadata (``VectorCollectionRecord``). Configured fallbacks apply only when
inheritance permits and a value cannot be resolved.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from contracts.enums import DistanceMetric
from domain.inheritance.errors import InheritanceError, InheritanceErrorType


class CollectionSchema(BaseModel):
    """Schema read from an EKIE-published Qdrant collection."""

    model_config = ConfigDict(frozen=True)

    collection: str = Field(min_length=1)
    dimension: int | None = Field(default=None, ge=0)
    distance_metric: DistanceMetric | None = None
    embedding_model: str | None = None
    embedding_version: int | None = Field(default=None, ge=0)


class EmbeddingProfile(BaseModel):
    """Resolved retrieval profile inherited from EKIE, used to query vectors."""

    model_config = ConfigDict(frozen=True)

    collection: str = Field(min_length=1)
    embedding_model: str = Field(min_length=1)
    dimension: int = Field(gt=0)
    distance_metric: DistanceMetric
    embedding_version: int | None = Field(default=None, ge=0)
    source: str = Field(min_length=1)


class SchemaReader(Protocol):
    """Reads the schema of an EKIE-published collection.

    Implementations return whatever they can resolve; unresolved fields are left
    as ``None`` so the resolver can apply configured fallbacks deterministically.
    """

    def read(self, collection: str) -> CollectionSchema:
        """Return the schema for ``collection``.

        Raises :class:`InheritanceError` with ``COLLECTION_UNAVAILABLE`` when the
        collection cannot be reached.
        """
        ...


class InheritanceSettingsLike(Protocol):
    """Structural view of the inheritance settings the resolver depends on."""

    allow_config_fallback: bool
    fallback_embedding_model: str
    fallback_dimension: int
    fallback_distance_metric: str


class InheritanceResolver:
    """Resolve the retrieval :class:`EmbeddingProfile` for a collection."""

    def __init__(
        self,
        reader: SchemaReader,
        *,
        allow_config_fallback: bool = True,
        fallback_embedding_model: str = "",
        fallback_dimension: int = 0,
        fallback_distance_metric: str = "cosine",
    ) -> None:
        self._reader = reader
        self._allow_config_fallback = allow_config_fallback
        self._fallback_embedding_model = fallback_embedding_model
        self._fallback_dimension = fallback_dimension
        self._fallback_distance_metric = fallback_distance_metric

    @classmethod
    def from_settings(
        cls, reader: SchemaReader, settings: InheritanceSettingsLike
    ) -> InheritanceResolver:
        """Build a resolver from the inheritance settings and a schema reader."""
        return cls(
            reader,
            allow_config_fallback=settings.allow_config_fallback,
            fallback_embedding_model=settings.fallback_embedding_model,
            fallback_dimension=settings.fallback_dimension,
            fallback_distance_metric=settings.fallback_distance_metric,
        )

    def resolve(self, collection: str) -> EmbeddingProfile:
        """Resolve the embedding profile for ``collection``.

        Reads the live collection schema and fills any unresolved field from
        configuration when ``allow_config_fallback`` is set. Raises
        :class:`InheritanceError` when a required value cannot be resolved.
        """
        schema = self._reader.read(collection)

        distance_metric = schema.distance_metric or self._fallback_distance()
        if distance_metric is None:
            raise InheritanceError(
                InheritanceErrorType.METRIC_UNRESOLVED,
                f"distance metric could not be inherited for collection {collection!r}",
            )

        dimension = schema.dimension or self._fallback_dimension_value()
        if not dimension:
            raise InheritanceError(
                InheritanceErrorType.DIMENSION_UNRESOLVED,
                f"vector dimension could not be inherited for collection {collection!r}",
            )

        embedding_model = schema.embedding_model or self._fallback_model()
        if not embedding_model:
            raise InheritanceError(
                InheritanceErrorType.MODEL_UNRESOLVED,
                f"embedding model could not be inherited for collection {collection!r}",
            )

        source = "inherited" if schema.embedding_model and schema.distance_metric else "hybrid"
        return EmbeddingProfile(
            collection=collection,
            embedding_model=embedding_model,
            dimension=dimension,
            distance_metric=distance_metric,
            embedding_version=schema.embedding_version,
            source=source,
        )

    def _fallback_distance(self) -> DistanceMetric | None:
        if not self._allow_config_fallback:
            return None
        return DistanceMetric(self._fallback_distance_metric)

    def _fallback_dimension_value(self) -> int:
        if not self._allow_config_fallback:
            return 0
        return self._fallback_dimension

    def _fallback_model(self) -> str:
        if not self._allow_config_fallback:
            return ""
        return self._fallback_embedding_model

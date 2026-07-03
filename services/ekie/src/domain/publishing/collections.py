"""Collection management: policy-driven assignment and schema (handbook 11.11)."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from domain.control_plane import Document
from domain.embedding.models import EmbeddingDocument
from domain.publishing.policy import PublishingPolicy


class CollectionSpec(BaseModel):
    """The enforced schema for a vector collection (handbook 11.11)."""

    model_config = {"frozen": True}

    name: str
    dimension: int = Field(gt=0)
    distance_metric: str


class CollectionResolver:
    """Assigns a document's vectors to a collection with an enforced schema.

    Collection names are derived from policy so application code never hardcodes
    them (handbook 11.11). The dimension and distance metric are taken from the
    embedding asset to guarantee schema consistency between embeddings and the
    vector database.
    """

    def __init__(self, policy: PublishingPolicy) -> None:
        self._policy = policy

    def resolve(
        self, document: Document, embedding_document: EmbeddingDocument
    ) -> CollectionSpec:
        """Return the collection schema for a document's embedding set."""
        name = self._policy.default_collection
        if self._policy.collection_strategy == "model_scoped":
            model_slug = _slug(embedding_document.model_name)
            name = (
                f"{name}__{embedding_document.provider}__"
                f"{model_slug}__d{embedding_document.dimension}"
            )
        return CollectionSpec(
            name=name,
            dimension=embedding_document.dimension,
            distance_metric=embedding_document.distance_metric.value,
        )


def _slug(value: str) -> str:
    """Return a Qdrant-safe model slug (lowercase alnum/underscore only)."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "model"

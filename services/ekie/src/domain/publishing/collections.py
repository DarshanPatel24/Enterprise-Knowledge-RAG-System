"""Collection management: policy-driven assignment and schema (handbook 11.11)."""

from __future__ import annotations

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
        return CollectionSpec(
            name=self._policy.default_collection,
            dimension=embedding_document.dimension,
            distance_metric=embedding_document.distance_metric.value,
        )

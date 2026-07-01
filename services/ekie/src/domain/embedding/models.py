"""Embedding asset, model spec, and lifecycle models (handbook 10.5, 10.20).

These models form the embedding contract consumed by the Vector Publishing
Framework (Chapter 11). They are EKIE-internal and intentionally not part of
packages/contracts, which carries only cross-service payloads. Persisted
embedding documents are deterministic: no wall-clock timestamps or durations
are included so identical chunks and models dedupe cleanly (ADR-022).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DistanceMetric(StrEnum):
    """Vector distance metric declared with an embedding model (handbook 10.5)."""

    COSINE = "cosine"
    DOT_PRODUCT = "dot_product"
    EUCLIDEAN = "euclidean"


class ModelStatus(StrEnum):
    """Governance status of an approved embedding model (handbook 10.7)."""

    ACTIVE = "active"
    APPROVED = "approved"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"


class EmbeddingStatus(StrEnum):
    """Managed embedding lifecycle states (handbook 10.20).

    Publishing states (PUBLISHED, VERIFIED) belong to the Vector Publishing
    Framework and are intentionally excluded here.
    """

    PENDING = "pending"
    GENERATING = "generating"
    VALIDATED = "validated"
    READY = "ready"
    FAILED = "failed"


class EmbeddingModelSpec(BaseModel):
    """A governed embedding model entry from the registry (handbook 10.7)."""

    model_config = {"frozen": True}

    name: str
    provider: str
    dimensions: int = Field(gt=0)
    distance_metric: DistanceMetric
    max_input_tokens: int = Field(gt=0)
    status: ModelStatus = ModelStatus.ACTIVE


class EmbeddingRecord(BaseModel):
    """A single chunk's embedding with governance linkage (handbook 10.5)."""

    model_config = {"frozen": True}

    embedding_id: str
    chunk_id: str
    chunk_content_hash: str
    token_count: int
    cost_estimate: float
    status: EmbeddingStatus
    values: list[float] = Field(default_factory=list)


class EmbeddingDocument(BaseModel):
    """The complete, versioned embedding set for a document (ADR-022)."""

    model_config = {"frozen": True}

    document_id: str
    source_markdown_version: int
    model_name: str
    provider: str
    dimension: int
    distance_metric: DistanceMetric
    embedding_count: int
    total_tokens: int
    records: list[EmbeddingRecord] = Field(default_factory=list)

    def canonical_json(self) -> bytes:
        """Return deterministic UTF-8 JSON bytes for immutable asset storage."""
        return self.model_dump_json(indent=2).encode("utf-8")

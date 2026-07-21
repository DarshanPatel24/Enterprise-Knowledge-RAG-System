"""Vector publishing models: sync states, points, metadata, and asset payload.

These models form the publishing contract between validated embedding assets and
the vector database. They are EKIE-internal and intentionally not part of
packages/contracts, which carries only cross-service payloads. Persisted
published-vector sets are deterministic: no wall-clock timestamps or durations
are included so identical embeddings and collections dedupe cleanly (ADR-027).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from domain.embedding.models import DistanceMetric


class SyncState(StrEnum):
    """Vector publishing lifecycle states (handbook 11.18)."""

    READY = "ready"
    QUEUED = "queued"
    PUBLISHING = "publishing"
    VERIFYING = "verifying"
    PUBLISHED = "published"
    VERIFIED = "verified"
    FAILED = "failed"
    RETRYING = "retrying"
    ROLLBACK = "rollback"
    ARCHIVED = "archived"


class VectorMetadata(BaseModel):
    """Metadata published alongside every vector (handbook 11.12).

    The mandatory governance fields (document_id, chunk_id, tenant_id,
    classification_clearance, distance_metric) enable downstream filtering and
    access control without additional joins. Enrichment fields are populated
    from the chunk set when available.
    """

    model_config = {"frozen": True}

    document_id: str
    chunk_id: str
    tenant_id: str
    classification_clearance: str
    distance_metric: DistanceMetric
    collection: str
    embedding_model: str
    embedding_version: int
    dimension: int
    repository_id: str = ""
    # The original document path/filename (e.g. "1/Integrity Installation
    # Guide.pdf.md") so citations can show a human-readable source instead of an
    # opaque id. Sourced from the control-plane Document; empty for legacy
    # vectors published before this field existed.
    source_path: str = ""
    # Product/source group derived from the leading folder of ``source_path`` (e.g.
    # "plantstate-integrity") so retrieval can be scoped or filtered by product.
    # Empty for root-level documents or vectors published before this field existed.
    source_group: str = ""
    section_id: str | None = None
    section_title: str | None = None
    language: str = ""
    # The chunk text itself, published so the retrieval engine (EKRE) can return
    # and rerank the actual passage. Sourced from the chunk set like the other
    # enrichment fields; empty only when that set is unavailable at publish time.
    content: str = ""


class VectorPoint(BaseModel):
    """A single vector with its stable identity and published metadata."""

    model_config = {"frozen": True}

    vector_id: str
    values: list[float] = Field(default_factory=list)
    metadata: VectorMetadata


class VectorRecord(BaseModel):
    """A persisted summary of one published vector for the managed asset."""

    model_config = {"frozen": True}

    vector_id: str
    chunk_id: str
    chunk_content_hash: str
    state: SyncState


class PublishedVectorSet(BaseModel):
    """The complete, versioned set of vectors published for a document."""

    model_config = {"frozen": True}

    document_id: str
    collection: str
    provider: str
    model_name: str
    distance_metric: DistanceMetric
    dimension: int
    vector_count: int
    source_embedding_version: int
    records: list[VectorRecord] = Field(default_factory=list)

    def canonical_json(self) -> bytes:
        """Return deterministic UTF-8 JSON bytes for immutable asset storage."""
        return self.model_dump_json(indent=2).encode("utf-8")

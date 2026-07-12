"""Retrieval context package and citation contracts produced by EKRE."""

from pydantic import Field

from contracts.base import VersionedContract


class Citation(VersionedContract):
    """Citation lineage that must survive the full retrieval pipeline."""

    document_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    # Human-readable section heading for the cited passage (e.g. "Windows
    # Authentication"). Optional so legacy candidates without it still validate.
    section_title: str | None = None


class RetrievalCandidate(VersionedContract):
    """A single ranked, explainable retrieval result."""

    citation: Citation
    content: str = Field(min_length=1)
    relevance_score: float = Field(ge=0.0, le=1.0)
    explanation: str | None = None


class RetrievalContextPackage(VersionedContract):
    """Structured retrieval result handed from EKRE to EKCP."""

    query: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    candidates: list[RetrievalCandidate] = Field(default_factory=list)
    security_filtered: bool = True

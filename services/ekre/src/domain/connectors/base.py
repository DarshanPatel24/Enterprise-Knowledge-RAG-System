"""Repository connector contract (handbook Chapter 22).

Retrieval workers communicate exclusively with connectors; they never touch a
repository API directly. Every connector exposes the same standardized search
operations and enforces the security clearance filter at the repository (data)
boundary, so unauthorized candidates never leave the repository layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from domain.query.models import MetadataFilter


class Capability(StrEnum):
    """Search capabilities a connector may advertise."""

    VECTOR_SEARCH = "vector_search"
    KEYWORD_SEARCH = "keyword_search"
    METADATA_SEARCH = "metadata_search"


class RepositoryDocument(BaseModel):
    """A standardized document returned by a repository connector."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    content: str
    source_path: str
    score: float = Field(ge=0.0)
    tenant_id: str = ""
    classification_clearance: str = "public"
    repository_id: str = ""
    section_id: str | None = None
    language: str | None = None


class RepositoryConnector(ABC):
    """Standardized interface to an enterprise knowledge repository.

    The ``allowed_clearances`` argument is the security filter applied at the
    repository boundary: only documents whose classification is within the set
    are ever returned, so unauthorized candidates never enter the pool.
    """

    @abstractmethod
    def capabilities(self) -> frozenset[Capability]:
        """Return the search capabilities this connector supports."""

    @abstractmethod
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
        """Execute a semantic search and return clearance-filtered documents."""

    @abstractmethod
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
        """Execute a lexical search and return clearance-filtered documents."""

    @abstractmethod
    def metadata_search(
        self,
        collection: str,
        metadata_filters: Sequence[MetadataFilter],
        *,
        limit: int,
        allowed_clearances: Sequence[str],
        tenant_id: str = "",
    ) -> list[RepositoryDocument]:
        """Execute a metadata search and return clearance-filtered documents."""

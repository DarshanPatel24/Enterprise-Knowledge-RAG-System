"""In-memory repository connector (local-first, deterministic).

A dependency-free connector used for offline execution, tests, and demos. It
indexes documents in memory and implements vector, keyword, and metadata search
deterministically, enforcing the clearance filter at the repository boundary.
Real deployments use the Qdrant connector; the contract is identical.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from domain.connectors.base import (
    Capability,
    RepositoryConnector,
    RepositoryDocument,
)
from domain.query.models import MetadataFilter


@dataclass(frozen=True)
class IndexedDocument:
    """A document stored in the in-memory index."""

    document_id: str
    chunk_id: str
    content: str
    source_path: str
    vector: tuple[float, ...]
    tenant_id: str = ""
    classification_clearance: str = "public"
    repository_id: str = "in-memory"
    section_id: str | None = None
    language: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class InMemoryRepositoryConnector(RepositoryConnector):
    """Deterministic in-memory connector supporting all search modes."""

    def __init__(self, documents: Sequence[IndexedDocument] = ()) -> None:
        self._documents: list[IndexedDocument] = list(documents)

    def index(self, document: IndexedDocument) -> None:
        """Add a document to the in-memory index."""
        self._documents.append(document)

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
        """Return the top-``limit`` documents by cosine similarity."""
        allowed = set(allowed_clearances)
        scored: list[tuple[float, IndexedDocument]] = []
        for doc in self._eligible(allowed, metadata_filters, tenant_id):
            score = _cosine(vector, doc.vector)
            if score > 0.0:
                scored.append((score, doc))
        scored.sort(key=lambda item: (-item[0], item[1].document_id, item[1].chunk_id))
        return [_to_document(doc, score) for score, doc in scored[:limit]]

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
        """Return documents ranked by exact term overlap in their content."""
        allowed = set(allowed_clearances)
        wanted = [term.lower() for term in terms if term]
        if not wanted:
            return []
        scored: list[tuple[float, IndexedDocument]] = []
        for doc in self._eligible(allowed, metadata_filters, tenant_id):
            haystack = doc.content.lower()
            matches = sum(1 for term in wanted if term in haystack)
            if matches:
                scored.append((matches / len(wanted), doc))
        scored.sort(key=lambda item: (-item[0], item[1].document_id, item[1].chunk_id))
        return [_to_document(doc, score) for score, doc in scored[:limit]]

    def metadata_search(
        self,
        collection: str,
        metadata_filters: Sequence[MetadataFilter],
        *,
        limit: int,
        allowed_clearances: Sequence[str],
        tenant_id: str = "",
    ) -> list[RepositoryDocument]:
        """Return documents matching all metadata filters."""
        allowed = set(allowed_clearances)
        if not metadata_filters:
            return []
        matched = list(self._eligible(allowed, metadata_filters, tenant_id))
        matched.sort(key=lambda doc: (doc.document_id, doc.chunk_id))
        return [_to_document(doc, 1.0) for doc in matched[:limit]]

    def _eligible(
        self,
        allowed: set[str],
        metadata_filters: Sequence[MetadataFilter],
        tenant_id: str = "",
    ) -> list[IndexedDocument]:
        return [
            doc
            for doc in self._documents
            if doc.classification_clearance in allowed
            and (not tenant_id or doc.tenant_id == tenant_id)
            and _matches_filters(doc, metadata_filters)
        ]


def _matches_filters(doc: IndexedDocument, filters: Sequence[MetadataFilter]) -> bool:
    for metadata_filter in filters:
        value = _attribute(doc, metadata_filter.field)
        if value is None or not _compare(value, metadata_filter.operator, metadata_filter.value):
            return False
    return True


def _attribute(doc: IndexedDocument, field_name: str) -> str | None:
    known = {
        "classification_clearance": doc.classification_clearance,
        "section_id": doc.section_id,
        "language": doc.language,
        "repository_id": doc.repository_id,
    }
    if field_name in known:
        return known[field_name]
    return doc.metadata.get(field_name)


def _compare(value: str, operator: str, target: str) -> bool:
    if operator == "gte":
        return value >= target
    if operator == "lte":
        return value <= target
    return value == target


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)


def _to_document(doc: IndexedDocument, score: float) -> RepositoryDocument:
    return RepositoryDocument(
        document_id=doc.document_id,
        chunk_id=doc.chunk_id,
        content=doc.content,
        source_path=doc.source_path,
        score=max(0.0, min(1.0, score)),
        tenant_id=doc.tenant_id,
        classification_clearance=doc.classification_clearance,
        repository_id=doc.repository_id,
        section_id=doc.section_id,
        language=doc.language,
    )

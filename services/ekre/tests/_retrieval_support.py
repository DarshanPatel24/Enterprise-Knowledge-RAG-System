"""Shared builders for the retrieval worker test suite (not collected)."""

from __future__ import annotations

from contracts.enums import ClassificationClearance
from contracts.security_context import SecurityContext
from domain.connectors import IndexedDocument, InMemoryRepositoryConnector
from domain.execution import RetrievalTask
from domain.query.models import MetadataFilter, RetrievalEngineType
from domain.retrieval import LocalHashEmbeddingAdapter

ADAPTER = LocalHashEmbeddingAdapter(16)


def indexed(
    document_id: str,
    chunk_id: str,
    text: str,
    *,
    clearance: str = "public",
    language: str | None = None,
    section_id: str | None = None,
    metadata: dict[str, str] | None = None,
) -> IndexedDocument:
    """Build an indexed document whose vector matches ``text`` for the adapter."""
    return IndexedDocument(
        document_id=document_id,
        chunk_id=chunk_id,
        content=text,
        source_path=f"/docs/{document_id}.md",
        vector=ADAPTER.embed(text),
        classification_clearance=clearance,
        language=language,
        section_id=section_id,
        metadata=metadata or {},
    )


def connector(*documents: IndexedDocument) -> InMemoryRepositoryConnector:
    """Build an in-memory connector seeded with ``documents``."""
    return InMemoryRepositoryConnector(documents)


def security_context(clearance: ClassificationClearance) -> SecurityContext:
    """Build a security context at ``clearance``."""
    return SecurityContext(
        user_id="analyst-1", tenant_id="tenant-a", classification_clearance=clearance
    )


def task(
    engine: RetrievalEngineType,
    query: str,
    *,
    candidate_limit: int = 5,
    metadata_filters: tuple[MetadataFilter, ...] = (),
) -> RetrievalTask:
    """Build a retrieval task for a worker test."""
    return RetrievalTask(
        task_id=f"t-{engine.value}",
        engine=engine,
        query=query,
        candidate_limit=candidate_limit,
        timeout_ms=150.0,
        parallel_group=0,
        tenant_id="tenant-a",
        metadata_filters=metadata_filters,
    )

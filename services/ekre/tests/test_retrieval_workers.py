"""Tests for the concrete retrieval workers (vector, keyword, metadata)."""

from __future__ import annotations

import pytest
from _retrieval_support import ADAPTER, connector, indexed, security_context, task

from contracts.enums import ClassificationClearance
from domain.query.models import MetadataFilter, RetrievalEngineType
from domain.retrieval import (
    KeywordRetrievalWorker,
    MetadataRetrievalWorker,
    RetrievalWorkerError,
    VectorRetrievalWorker,
)


def test_vector_worker_retrieves_and_normalizes() -> None:
    conn = connector(indexed("d1", "c1", "refinery shutdown"))
    worker = VectorRetrievalWorker(conn, ADAPTER, collection="c")
    candidates = worker.retrieve(
        task(RetrievalEngineType.VECTOR, "refinery shutdown"),
        security_context=security_context(ClassificationClearance.INTERNAL),
    )
    assert candidates[0].citation.document_id == "d1"
    assert candidates[0].explanation == "vector similarity"


def test_vector_worker_enforces_clearance() -> None:
    conn = connector(
        indexed("d1", "c1", "topic", clearance="public"),
        indexed("d2", "c2", "topic", clearance="restricted"),
    )
    worker = VectorRetrievalWorker(conn, ADAPTER, collection="c")
    candidates = worker.retrieve(
        task(RetrievalEngineType.VECTOR, "topic"),
        security_context=security_context(ClassificationClearance.PUBLIC),
    )
    ids = {c.citation.document_id for c in candidates}
    assert ids == {"d1"}


def test_vector_worker_requires_security_context() -> None:
    worker = VectorRetrievalWorker(connector(), ADAPTER, collection="c")
    with pytest.raises(RetrievalWorkerError):
        worker.retrieve(task(RetrievalEngineType.VECTOR, "q"), security_context=None)


def test_keyword_worker_matches_terms() -> None:
    conn = connector(indexed("d1", "c1", "vpn setup guide"))
    worker = KeywordRetrievalWorker(conn, collection="c")
    candidates = worker.retrieve(
        task(RetrievalEngineType.KEYWORD, "vpn guide"),
        security_context=security_context(ClassificationClearance.PUBLIC),
    )
    assert candidates[0].citation.document_id == "d1"
    assert candidates[0].explanation == "keyword match"


def test_metadata_worker_matches_filters() -> None:
    conn = connector(
        indexed("d1", "c1", "text", language="en"),
        indexed("d2", "c2", "text", language="fr"),
    )
    worker = MetadataRetrievalWorker(conn, collection="c")
    candidates = worker.retrieve(
        task(
            RetrievalEngineType.METADATA,
            "text",
            metadata_filters=(MetadataFilter(field="language", operator="eq", value="fr"),),
        ),
        security_context=security_context(ClassificationClearance.PUBLIC),
    )
    assert [c.citation.document_id for c in candidates] == ["d2"]

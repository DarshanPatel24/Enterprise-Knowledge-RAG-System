"""Tests for the query embedding adapters and the security clearance filter."""

from __future__ import annotations

import math

import pytest
from _retrieval_support import connector, indexed

from contracts.enums import ClassificationClearance
from contracts.security_context import SecurityContext
from domain.retrieval import (
    LocalHashEmbeddingAdapter,
    RetrievalWorkerError,
    enforce_clearance,
    enforce_tenant,
    resolve_allowed_clearances,
)


def test_local_hash_adapter_is_deterministic_and_normalized() -> None:
    adapter = LocalHashEmbeddingAdapter(32)
    first = adapter.embed("hello world")
    second = adapter.embed("hello world")
    assert first == second
    assert len(first) == 32
    assert math.isclose(math.sqrt(sum(v * v for v in first)), 1.0, rel_tol=1e-9)


def test_local_hash_adapter_rejects_bad_dimension() -> None:
    with pytest.raises(RetrievalWorkerError):
        LocalHashEmbeddingAdapter(0)


def test_allowed_clearances_are_cumulative() -> None:
    ctx = SecurityContext(
        user_id="u",
        tenant_id="t",
        classification_clearance=ClassificationClearance.CONFIDENTIAL,
    )
    allowed = resolve_allowed_clearances(ctx, require_security_context=True)
    assert allowed == ("public", "internal", "confidential")


def test_missing_context_required_raises() -> None:
    with pytest.raises(RetrievalWorkerError):
        resolve_allowed_clearances(None, require_security_context=True)


def test_missing_context_optional_returns_public() -> None:
    allowed = resolve_allowed_clearances(None, require_security_context=False)
    assert allowed == ("public",)


def test_enforce_clearance_drops_unauthorized() -> None:
    from _retrieval_support import ADAPTER

    conn = connector(
        indexed("d1", "c1", "text", clearance="public"),
        indexed("d2", "c2", "text", clearance="restricted"),
    )
    docs = conn.vector_search(
        "c",
        ADAPTER.embed("text"),
        limit=5,
        allowed_clearances=["public", "restricted"],
    )
    filtered = enforce_clearance(docs, ["public"])
    assert all(doc.classification_clearance == "public" for doc in filtered)
    assert filtered


def test_enforce_tenant_drops_other_tenants() -> None:
    from _retrieval_support import ADAPTER

    conn = connector(
        indexed("d1", "c1", "text", tenant_id="tenant-a"),
        indexed("d2", "c2", "text", tenant_id="tenant-b"),
    )
    docs = conn.vector_search(
        "c",
        ADAPTER.embed("text"),
        limit=5,
        allowed_clearances=["public"],
    )
    filtered = enforce_tenant(docs, "tenant-a")
    assert {doc.document_id for doc in filtered} == {"d1"}


def test_enforce_tenant_empty_tenant_is_noop() -> None:
    from _retrieval_support import ADAPTER

    conn = connector(indexed("d1", "c1", "text", tenant_id="tenant-a"))
    docs = conn.vector_search("c", ADAPTER.embed("text"), limit=5, allowed_clearances=["public"])
    assert enforce_tenant(docs, "") == docs

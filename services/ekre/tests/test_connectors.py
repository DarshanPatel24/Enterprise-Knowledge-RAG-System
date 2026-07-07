"""Tests for the in-memory repository connector (search + clearance boundary)."""

from __future__ import annotations

from _retrieval_support import ADAPTER, connector, indexed

from domain.connectors import Capability
from domain.query.models import MetadataFilter


def test_capabilities() -> None:
    caps = connector().capabilities()
    assert Capability.VECTOR_SEARCH in caps
    assert Capability.KEYWORD_SEARCH in caps
    assert Capability.METADATA_SEARCH in caps


def test_vector_search_returns_similar_document() -> None:
    conn = connector(indexed("d1", "c1", "refinery shutdown procedure"))
    vector = ADAPTER.embed("refinery shutdown procedure")
    results = conn.vector_search(
        "c", vector, limit=5, allowed_clearances=["public"]
    )
    assert results[0].document_id == "d1"
    assert results[0].score > 0.99


def test_clearance_filter_at_boundary() -> None:
    conn = connector(
        indexed("d1", "c1", "public doc", clearance="public"),
        indexed("d2", "c2", "secret doc", clearance="restricted"),
    )
    vector = ADAPTER.embed("public doc")
    results = conn.vector_search("c", vector, limit=5, allowed_clearances=["public"])
    ids = {doc.document_id for doc in results}
    assert "d2" not in ids


def test_keyword_search_scores_term_overlap() -> None:
    conn = connector(
        indexed("d1", "c1", "vpn setup guide"),
        indexed("d2", "c2", "unrelated content"),
    )
    results = conn.keyword_search(
        "c", ["vpn", "guide"], limit=5, allowed_clearances=["public"]
    )
    assert results[0].document_id == "d1"


def test_metadata_search_matches_filters() -> None:
    conn = connector(
        indexed("d1", "c1", "text", language="en"),
        indexed("d2", "c2", "text", language="fr"),
    )
    results = conn.metadata_search(
        "c",
        [MetadataFilter(field="language", operator="eq", value="fr")],
        limit=5,
        allowed_clearances=["public"],
    )
    assert [doc.document_id for doc in results] == ["d2"]

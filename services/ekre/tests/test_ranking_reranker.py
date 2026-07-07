"""Tests for the reranker seam (identity default + disabled LLM fallback)."""

from __future__ import annotations

from types import SimpleNamespace

from domain.ranking import IdentityReranker, LlmReranker
from domain.ranking.reranker import _reconcile


def test_identity_reranker_preserves_order() -> None:
    reranker = IdentityReranker()
    assert reranker.enabled is False
    items = [("a", "x"), ("b", "y"), ("c", "z")]
    assert reranker.rerank("q", items) == ["a", "b", "c"]


def test_disabled_llm_reranker_returns_input_order() -> None:
    config = SimpleNamespace(
        enable_llm_reranker=False,
        llm_provider="ollama",
        llm_model="m",
        llm_base_url="http://127.0.0.1:1",
        llm_temperature=0.0,
    )
    reranker = LlmReranker(config)
    assert reranker.enabled is False
    assert reranker.rerank("q", [("a", "x"), ("b", "y")]) == ["a", "b"]


def test_reconcile_keeps_known_and_appends_missing() -> None:
    # Model returned an unknown id and dropped one -> reconcile repairs the order.
    result = _reconcile(["c", "z", "a"], ["a", "b", "c"])
    assert result == ["c", "a", "b"]

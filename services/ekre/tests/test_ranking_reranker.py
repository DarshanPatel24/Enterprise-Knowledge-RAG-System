"""Tests for the reranker seam (identity default + cross-encoder reranker)."""

from __future__ import annotations

from types import SimpleNamespace

from domain.ranking import CrossEncoderReranker, IdentityReranker
from domain.ranking.reranker import _order_by_scores


def _config(**overrides: object) -> SimpleNamespace:
    base = {
        "enable_reranker": True,
        "reranker_model": "Qwen/Qwen3-VL-Reranker-2B",
        "reranker_device": "auto",
        "reranker_torch_dtype": "auto",
        "reranker_trust_remote_code": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_identity_reranker_preserves_order() -> None:
    reranker = IdentityReranker()
    assert reranker.enabled is False
    items = [("a", "x"), ("b", "y"), ("c", "z")]
    assert reranker.rerank("q", items) == ["a", "b", "c"]


def test_cross_encoder_reranker_enabled_when_configured() -> None:
    assert CrossEncoderReranker(_config()).enabled is True


def test_cross_encoder_reranker_disabled_without_flag() -> None:
    reranker = CrossEncoderReranker(_config(enable_reranker=False))
    assert reranker.enabled is False
    assert reranker.rerank("q", [("a", "x"), ("b", "y")]) == ["a", "b"]


def test_cross_encoder_reranker_disabled_without_model() -> None:
    reranker = CrossEncoderReranker(_config(reranker_model=""))
    assert reranker.enabled is False


def test_cross_encoder_reranker_orders_by_injected_scores() -> None:
    reranker = CrossEncoderReranker(_config())
    reranker._model = SimpleNamespace(predict=lambda pairs: [0.1, 0.9, 0.5])
    order = reranker.rerank("q", [("a", "x"), ("b", "y"), ("c", "z")])
    assert order == ["b", "c", "a"]


def test_cross_encoder_reranker_degrades_on_scoring_error() -> None:
    def _boom(_pairs: object) -> list[float]:
        raise RuntimeError("model unavailable")

    reranker = CrossEncoderReranker(_config())
    reranker._model = SimpleNamespace(predict=_boom)
    assert reranker.rerank("q", [("a", "x"), ("b", "y")]) == ["a", "b"]


def test_order_by_scores_sorts_descending_with_stable_tie_break() -> None:
    ids = ["a", "b", "c", "d"]
    scores = [0.2, 0.8, 0.2, 0.8]
    # Ties keep the original relative order (b before d, a before c).
    assert _order_by_scores(ids, scores) == ["b", "d", "a", "c"]


def test_order_by_scores_returns_input_on_length_mismatch() -> None:
    assert _order_by_scores(["a", "b"], [0.9]) == ["a", "b"]

"""Tests for the HuggingFace embedding provider's lazy model loading.

The provider must not load its (multi-GB, often GPU) model at construction, so
that the composition root can build it in every process (API and workers)
without pinning a redundant copy into processes that never embed.
"""

from __future__ import annotations

import pytest

import domain.embedding.providers.huggingface as hf_mod
from domain.embedding.providers.base import EmbeddingProviderError
from domain.integrations.langchain_resources import LangChainResourceError


class _FakeEmbeddings:
    def __init__(self) -> None:
        self.calls = 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


def test_provider_does_not_load_model_on_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_calls = {"n": 0}

    def _fake_build(provider: str, model: str, **kwargs: object) -> _FakeEmbeddings:
        build_calls["n"] += 1
        return _FakeEmbeddings()

    monkeypatch.setattr(hf_mod, "build_embeddings", _fake_build)

    provider = hf_mod.HuggingFaceEmbeddingProvider(
        "some/model", model_kwargs={"device": "cuda"}
    )
    assert build_calls["n"] == 0  # construction is cheap — no model load

    vectors = provider.embed(["a", "b"], dimension=4, normalize=True)
    assert build_calls["n"] == 1  # loaded lazily on first embed
    assert len(vectors) == 2
    assert len(vectors[0]) == 4

    provider.embed(["c"], dimension=4, normalize=True)
    assert build_calls["n"] == 1  # model is cached, not rebuilt


def test_provider_maps_load_error_on_first_embed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(provider: str, model: str, **kwargs: object) -> object:
        raise LangChainResourceError("langchain-huggingface is not installed")

    monkeypatch.setattr(hf_mod, "build_embeddings", _boom)

    # Construction succeeds even when dependencies are missing (no load yet).
    provider = hf_mod.HuggingFaceEmbeddingProvider("some/model")

    with pytest.raises(EmbeddingProviderError):
        provider.embed(["x"], dimension=4, normalize=True)

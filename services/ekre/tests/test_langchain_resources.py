"""Tests for the LangChain retrieval resource seam (offline-safe)."""

from __future__ import annotations

import importlib.util
from typing import Any

import pytest

from domain.integrations import (
    LangChainResourceError,
    build_embeddings,
    build_retriever,
    format_candidates,
)


class _FakeDoc:
    def __init__(self, content: str) -> None:
        self.page_content = content


class _FakeVectorStore:
    def as_retriever(self, *, search_type: str, search_kwargs: dict[str, Any]) -> object:
        self.search_type = search_type
        self.search_kwargs = search_kwargs
        return ("retriever", search_type, search_kwargs)


def test_build_embeddings_rejects_unknown_provider() -> None:
    with pytest.raises(LangChainResourceError):
        build_embeddings("local", "some-model")


def test_format_candidates_joins_page_content() -> None:
    merged = format_candidates([_FakeDoc("alpha"), _FakeDoc("beta")])
    assert merged == "alpha\n\nbeta"


def test_build_retriever_passes_search_kwargs() -> None:
    store = _FakeVectorStore()
    retriever = build_retriever(store, search_type="similarity", k=7)  # type: ignore[arg-type]
    assert retriever == ("retriever", "similarity", {"k": 7})


@pytest.mark.skipif(
    importlib.util.find_spec("langchain_ollama") is None,
    reason="langchain-ollama not installed",
)
def test_build_embeddings_ollama_constructs() -> None:
    embeddings = build_embeddings("ollama", "nomic-embed-text")
    assert embeddings is not None

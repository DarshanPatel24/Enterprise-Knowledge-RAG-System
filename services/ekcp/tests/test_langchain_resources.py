"""Tests for the LangChain chat-model seam and provider registry selection."""

from __future__ import annotations

import importlib.util

import pytest

from domain.gateway import (
    DeterministicEchoProvider,
    LangChainChatProvider,
    default_provider_registry,
    provider_registry_from_settings,
)
from domain.integrations import LangChainResourceError, build_chat_model


def test_build_chat_model_rejects_unknown_provider() -> None:
    with pytest.raises(LangChainResourceError):
        build_chat_model("unknown", "model")


def test_default_provider_registry_is_deterministic_only() -> None:
    registry = default_provider_registry()
    assert set(registry) == {"deterministic"}
    assert isinstance(registry["deterministic"], DeterministicEchoProvider)


def test_provider_registry_adds_langchain_when_selected() -> None:
    registry = provider_registry_from_settings("langchain")
    assert "langchain" in registry
    assert isinstance(registry["langchain"], LangChainChatProvider)


@pytest.mark.skipif(
    importlib.util.find_spec("langchain_ollama") is None,
    reason="langchain-ollama not installed",
)
def test_build_ollama_chat_model_constructs() -> None:
    model = build_chat_model("ollama", "llama3.1", base_url="http://localhost:11434")
    assert hasattr(model, "invoke")

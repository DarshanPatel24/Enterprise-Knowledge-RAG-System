"""Unit tests for the Ollama embedding provider and settings-driven registry (EKIE-S5-5)."""

import importlib.util
from dataclasses import dataclass

import pytest

from domain.embedding import (
    EmbeddingProviderError,
    LocalHashEmbeddingProvider,
    OllamaEmbeddingProvider,
    default_provider_registry,
    provider_registry_from_settings,
)


@dataclass
class _EmbeddingProviderSettings:
    provider: str
    default_model: str = "nomic-embed-text"
    ollama_base_url: str = "http://localhost:11434"
    request_timeout_seconds: float = 60.0


def test_ollama_provider_name() -> None:
    assert OllamaEmbeddingProvider("nomic-embed-text").name == "ollama"


def test_ollama_provider_requires_model_name() -> None:
    with pytest.raises(EmbeddingProviderError):
        OllamaEmbeddingProvider("")


def test_ollama_provider_rejects_non_positive_dimension() -> None:
    provider = OllamaEmbeddingProvider("nomic-embed-text")
    with pytest.raises(EmbeddingProviderError):
        provider.embed(["text"], dimension=0, normalize=False)


def test_default_registry_has_local_but_not_ollama() -> None:
    registry = default_provider_registry()
    assert registry.get("local").name == "local"
    with pytest.raises(EmbeddingProviderError):
        registry.get("ollama")


def test_registry_from_settings_local_excludes_ollama() -> None:
    registry = provider_registry_from_settings(_EmbeddingProviderSettings(provider="local"))
    assert isinstance(registry.get("local"), LocalHashEmbeddingProvider)
    with pytest.raises(EmbeddingProviderError):
        registry.get("ollama")


def test_registry_from_settings_selects_ollama() -> None:
    registry = provider_registry_from_settings(_EmbeddingProviderSettings(provider="ollama"))
    assert isinstance(registry.get("ollama"), OllamaEmbeddingProvider)
    assert registry.get("local").name == "local"


@pytest.mark.skipif(
    importlib.util.find_spec("ollama") is not None,
    reason="the 'ollama' package is installed; the missing-package path is not exercised",
)
def test_ollama_embed_without_package_raises_domain_error() -> None:
    provider = OllamaEmbeddingProvider("nomic-embed-text")
    with pytest.raises(EmbeddingProviderError):
        provider.embed(["text"], dimension=8, normalize=False)

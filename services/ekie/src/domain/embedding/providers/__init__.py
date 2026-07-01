"""Embedding provider registry and selection (handbook 10.6)."""

from __future__ import annotations

from domain.embedding.providers.base import EmbeddingProvider, EmbeddingProviderError
from domain.embedding.providers.local import LocalHashEmbeddingProvider


class EmbeddingProviderRegistry:
    """Resolves a provider name to its plugin implementation (ADR-021)."""

    def __init__(self, providers: list[EmbeddingProvider]) -> None:
        self._providers = {provider.name: provider for provider in providers}

    def get(self, name: str) -> EmbeddingProvider:
        """Return the provider registered under ``name``."""
        provider = self._providers.get(name)
        if provider is None:
            raise EmbeddingProviderError(f"no embedding provider registered for {name!r}")
        return provider

    def register(self, provider: EmbeddingProvider) -> None:
        """Register or override a provider plugin."""
        self._providers[provider.name] = provider


def default_provider_registry() -> EmbeddingProviderRegistry:
    """Return the default registry with the built-in local provider."""
    return EmbeddingProviderRegistry([LocalHashEmbeddingProvider()])


__all__ = [
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "EmbeddingProviderRegistry",
    "LocalHashEmbeddingProvider",
    "default_provider_registry",
]

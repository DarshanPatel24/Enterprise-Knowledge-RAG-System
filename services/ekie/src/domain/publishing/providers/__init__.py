"""Vector provider registry and selection (handbook 11.5, ADR-028)."""

from __future__ import annotations

from typing import Protocol

from domain.publishing.providers.base import VectorProvider, VectorProviderError
from domain.publishing.providers.local import InMemoryVectorProvider
from domain.publishing.providers.qdrant import QdrantVectorProvider


class VectorProviderRegistry:
    """Resolves a provider name to its vector database plugin (ADR-028)."""

    def __init__(self, providers: list[VectorProvider]) -> None:
        self._providers = {provider.name: provider for provider in providers}

    def get(self, name: str) -> VectorProvider:
        """Return the provider registered under ``name``."""
        provider = self._providers.get(name)
        if provider is None:
            raise VectorProviderError(f"no vector provider registered for {name!r}")
        return provider

    def register(self, provider: VectorProvider) -> None:
        """Register or override a provider plugin."""
        self._providers[provider.name] = provider


class VectorProviderSettingsLike(Protocol):
    """Structural type for the publishing settings that select a provider."""

    provider: str


class QdrantConnectionLike(Protocol):
    """Structural type for the canonical Qdrant connection settings."""

    host: str
    port: int
    request_timeout_seconds: float


def default_provider_registry() -> VectorProviderRegistry:
    """Return the default registry with the built-in local vector provider."""
    return VectorProviderRegistry([InMemoryVectorProvider()])


def provider_registry_from_settings(
    settings: VectorProviderSettingsLike,
    qdrant: QdrantConnectionLike,
) -> VectorProviderRegistry:
    """Build a registry from configuration.

    The in-memory provider is always registered so the offline path remains
    available. A real Qdrant provider is added only when it is the selected
    provider, and its connection is sourced from the canonical Qdrant settings
    rather than duplicated on the publishing policy.
    """
    providers: list[VectorProvider] = [InMemoryVectorProvider()]
    if settings.provider == QdrantVectorProvider.name:
        providers.append(
            QdrantVectorProvider(
                host=qdrant.host,
                port=qdrant.port,
                request_timeout_seconds=qdrant.request_timeout_seconds,
            )
        )
    return VectorProviderRegistry(providers)


__all__ = [
    "InMemoryVectorProvider",
    "QdrantConnectionLike",
    "QdrantVectorProvider",
    "VectorProvider",
    "VectorProviderError",
    "VectorProviderRegistry",
    "VectorProviderSettingsLike",
    "default_provider_registry",
    "provider_registry_from_settings",
]

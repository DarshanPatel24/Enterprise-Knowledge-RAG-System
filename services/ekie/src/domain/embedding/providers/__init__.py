"""Embedding provider registry and selection (handbook 10.6)."""

from __future__ import annotations

from typing import Protocol

from domain.embedding.providers.base import EmbeddingProvider, EmbeddingProviderError
from domain.embedding.providers.local import LocalHashEmbeddingProvider
from domain.embedding.providers.ollama import OllamaEmbeddingProvider


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


class EmbeddingProviderSettingsLike(Protocol):
    """Structural type for the settings needed to build the provider registry."""

    provider: str
    default_model: str
    ollama_base_url: str
    request_timeout_seconds: float
    device: str
    torch_dtype: str


def default_provider_registry() -> EmbeddingProviderRegistry:
    """Return the default registry with the built-in local provider."""
    return EmbeddingProviderRegistry([LocalHashEmbeddingProvider()])


def provider_registry_from_settings(
    settings: EmbeddingProviderSettingsLike,
) -> EmbeddingProviderRegistry:
    """Build a registry from configuration.

    The deterministic local provider is always registered so the offline path
    remains available. A real Ollama or HuggingFace provider is added and bound to the
    configured model only when it is the selected provider, keeping the default
    path free of the optional dependencies.
    """
    providers: list[EmbeddingProvider] = [LocalHashEmbeddingProvider()]
    if settings.provider == OllamaEmbeddingProvider.name:
        providers.append(
            OllamaEmbeddingProvider(
                model=settings.default_model,
                base_url=settings.ollama_base_url,
                request_timeout_seconds=settings.request_timeout_seconds,
            )
        )
    elif settings.provider == "huggingface":
        from domain.embedding.providers.huggingface import HuggingFaceEmbeddingProvider

        # Build sentence-transformers kwargs for device/precision. Leaving either
        # at "auto" preserves the library defaults (GPU auto-detect, fp32); set
        # torch_dtype to "float16" to fit large models on limited-VRAM GPUs.
        st_kwargs: dict[str, object] = {}
        device = getattr(settings, "device", "auto")
        torch_dtype = getattr(settings, "torch_dtype", "auto")
        if device and device != "auto":
            st_kwargs["device"] = device
        if torch_dtype and torch_dtype != "auto":
            st_kwargs["model_kwargs"] = {"torch_dtype": torch_dtype}
        provider_kwargs = {"model_kwargs": st_kwargs} if st_kwargs else {}
        providers.append(
            HuggingFaceEmbeddingProvider(
                model_name=settings.default_model,
                **provider_kwargs,
            )
        )
    return EmbeddingProviderRegistry(providers)


__all__ = [
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "EmbeddingProviderRegistry",
    "EmbeddingProviderSettingsLike",
    "LocalHashEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "default_provider_registry",
    "provider_registry_from_settings",
]

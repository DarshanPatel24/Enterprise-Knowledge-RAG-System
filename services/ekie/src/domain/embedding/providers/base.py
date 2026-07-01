"""Embedding provider abstraction (handbook 10.6, ADR-021).

Providers are accessed exclusively through this interface so that embedding
technologies can be replaced without modifying the framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar


class EmbeddingProviderError(RuntimeError):
    """Raised when a provider fails to generate embeddings."""


class EmbeddingProvider(ABC):
    """A pluggable embedding provider (handbook 10.6, ADR-021)."""

    name: ClassVar[str]

    @abstractmethod
    def embed(
        self, texts: list[str], *, dimension: int, normalize: bool
    ) -> list[list[float]]:
        """Return one vector of ``dimension`` floats per input text.

        Implementations must be deterministic for identical inputs so that
        embedding assets dedupe correctly across regeneration (ADR-022).
        """

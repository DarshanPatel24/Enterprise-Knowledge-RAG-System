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

    def warm_up(self) -> None:
        """Eagerly load any deferred model so the first embed is not delayed.

        The default is a no-op; providers that lazily load a heavy (often GPU)
        model override this to force the load at process startup, surfacing any
        model-load failure immediately instead of on the first ingested chunk.
        """
        return None

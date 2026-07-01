"""Ollama-backed embedding provider (real semantic vectors, local-first).

Generates embeddings from a locally hosted Ollama model (for example
``nomic-embed-text`` or ``mxbai-embed-large``) through the same provider
contract as the deterministic hash provider (ADR-021). The model is accessed
directly via the ``ollama`` client rather than through LangChain, keeping this
seam free of double abstraction. The deterministic ``LocalHashEmbeddingProvider``
remains the default so the pipeline stays fully offline and reproducible unless
this provider is explicitly selected by configuration.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar, Protocol, cast

from domain.embedding.providers.base import EmbeddingProvider, EmbeddingProviderError

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_TIMEOUT_SECONDS = 60.0


if TYPE_CHECKING:

    class _OllamaClient(Protocol):
        """Structural type for the subset of the Ollama client used here."""

        def embeddings(self, *, model: str, prompt: str) -> dict[str, list[float]]: ...


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by a local Ollama model (handbook 10.6)."""

    name: ClassVar[str] = "ollama"

    def __init__(
        self,
        model: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        request_timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Bind the provider to a configured Ollama model and endpoint."""
        if not model:
            raise EmbeddingProviderError("ollama embedding model name must be provided")
        self._model = model
        self._base_url = base_url
        self._request_timeout_seconds = request_timeout_seconds

    def embed(
        self, texts: list[str], *, dimension: int, normalize: bool
    ) -> list[list[float]]:
        """Return one Ollama-generated vector of ``dimension`` floats per text."""
        if dimension <= 0:
            raise EmbeddingProviderError("dimension must be a positive integer")
        client = self._build_client()
        return [self._embed_one(client, text, dimension, normalize) for text in texts]

    def _build_client(self) -> _OllamaClient:
        try:
            import ollama
        except ImportError as exc:
            raise EmbeddingProviderError(
                "the 'ollama' package is required for the 'ollama' embedding "
                "provider; install it or use the default 'local' provider"
            ) from exc
        client = ollama.Client(host=self._base_url, timeout=self._request_timeout_seconds)
        return cast("_OllamaClient", client)

    def _embed_one(
        self, client: _OllamaClient, text: str, dimension: int, normalize: bool
    ) -> list[float]:
        try:
            response = client.embeddings(model=self._model, prompt=text or "\x00")
        except Exception as exc:  # external client boundary: normalize to domain error
            raise EmbeddingProviderError(
                f"ollama embedding request failed for model {self._model!r}: {exc}"
            ) from exc
        vector = [float(value) for value in response["embedding"]]
        if len(vector) != dimension:
            raise EmbeddingProviderError(
                f"ollama model {self._model!r} returned {len(vector)} dimensions; "
                f"configuration expects {dimension}"
            )
        return self._normalize(vector) if normalize else vector

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0.0:
            return vector
        return [value / norm for value in vector]

"""Ollama-backed embedding provider (real semantic vectors, local-first).

Generates embeddings from a locally hosted Ollama model (for example
``nomic-embed-text`` or ``mxbai-embed-large``) through the shared LangChain
resource template, so the embedding model is constructed in one place and is
easy to swap later. The provider preserves the engine contract (dimension
validation and optional L2 normalization). The deterministic
``LocalHashEmbeddingProvider`` remains the default so the pipeline stays fully
offline and reproducible unless this provider is explicitly selected by
configuration.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

from domain.embedding.providers.base import EmbeddingProvider, EmbeddingProviderError
from domain.integrations.langchain_resources import (
    LangChainResourceError,
    build_embeddings,
)

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_TIMEOUT_SECONDS = 60.0


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
        self._embeddings: Embeddings | None = None

    def embed(
        self, texts: list[str], *, dimension: int, normalize: bool
    ) -> list[list[float]]:
        """Return one Ollama-generated vector of ``dimension`` floats per text."""
        if dimension <= 0:
            raise EmbeddingProviderError("dimension must be a positive integer")
        embeddings = self._build()
        try:
            raw_vectors = embeddings.embed_documents(texts)
        except Exception as exc:  # external client boundary: normalize to domain error
            raise EmbeddingProviderError(
                f"ollama embedding request failed for model {self._model!r}: {exc}"
            ) from exc
        return [self._finalize(vector, dimension, normalize) for vector in raw_vectors]

    def _build(self) -> Embeddings:
        if self._embeddings is None:
            try:
                self._embeddings = build_embeddings(
                    "ollama", self._model, base_url=self._base_url
                )
            except LangChainResourceError as exc:
                raise EmbeddingProviderError(str(exc)) from exc
        return self._embeddings

    def _finalize(
        self, vector: list[float], dimension: int, normalize: bool
    ) -> list[float]:
        values = [float(value) for value in vector]
        if len(values) != dimension:
            raise EmbeddingProviderError(
                f"ollama model {self._model!r} returned {len(values)} dimensions; "
                f"configuration expects {dimension}"
            )
        return self._normalize(values) if normalize else values

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0.0:
            return vector
        return [value / norm for value in vector]

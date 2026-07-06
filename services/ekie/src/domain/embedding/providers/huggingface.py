"""HuggingFace embedding provider for generating vector representations.

Loads and executes sentence-transformer models locally through the shared
LangChain resource template. The dependency is lazy-loaded (inside the template)
so it does not bloat the offline base image when another provider (Ollama or
LocalHash) is used instead.
"""

from __future__ import annotations

from typing import Any

from domain.embedding.providers.base import EmbeddingProvider, EmbeddingProviderError
from domain.integrations.langchain_resources import (
    LangChainResourceError,
    build_embeddings,
)


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Generates embeddings using local HuggingFace models."""

    name = "huggingface"

    def __init__(self, model_name: str, **kwargs: Any) -> None:  # noqa: ANN401 - passthrough model kwargs
        try:
            self._embeddings = build_embeddings("huggingface", model_name, **kwargs)
        except LangChainResourceError as exc:
            raise EmbeddingProviderError(str(exc)) from exc
        self._model_name = model_name

    def embed(
        self, texts: list[str], *, dimension: int, normalize: bool
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            vectors = self._embeddings.embed_documents(texts)

            # Truncate dimensions if the engine's model spec requests fewer than
            # the model produces; engine-side validation checks normalization.
            if dimension is not None:
                vectors = [v[:dimension] for v in vectors]

            return vectors
        except Exception as exc:
            raise EmbeddingProviderError(
                f"HuggingFace embedding generation failed: {exc}"
            ) from exc

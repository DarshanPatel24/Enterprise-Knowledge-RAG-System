"""HuggingFace embedding provider for generating vector representations.

Uses ``langchain-huggingface`` to load and execute sentence-transformer models
locally. The dependency is lazy-loaded so it does not bloat the offline base image
if another provider (like Ollama or LocalHash) is used instead.
"""

from __future__ import annotations

from typing import Any

from domain.embedding.providers.base import EmbeddingProvider, EmbeddingProviderError


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Generates embeddings using local HuggingFace models."""

    name = "huggingface"

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError as exc:
            raise EmbeddingProviderError(
                "langchain-huggingface is not installed; install it to use HuggingFace embeddings"
            ) from exc

        self._model_name = model_name
        self._embeddings = HuggingFaceEmbeddings(model_name=model_name, **kwargs)

    def embed(
        self, texts: list[str], *, dimension: int, normalize: bool
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            vectors = self._embeddings.embed_documents(texts)
            
            # Sentence transformers encode_kwargs handles normalize, but if it wasn't
            # applied, the engine validation will check it.
            # Truncating dimensions if requested by the engine model spec.
            if dimension is not None:
                vectors = [v[:dimension] for v in vectors]
                
            return vectors
        except Exception as exc:
            raise EmbeddingProviderError(
                f"HuggingFace embedding generation failed: {exc}"
            ) from exc

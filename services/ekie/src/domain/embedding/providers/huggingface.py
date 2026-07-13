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
        # Defer model loading until the first embed call. The composition root
        # builds this provider in EVERY process (API and workers), but only the
        # process that actually embeds should pay the (multi-GB, often GPU) cost.
        # Eager loading here would pin a second copy of the model into the API —
        # wasted memory and, on small GPUs, out-of-memory contention with the
        # ingest worker that does the real embedding.
        self._model_name = model_name
        self._kwargs = kwargs
        self._embeddings: Any | None = None

    def _get_embeddings(self) -> Any:  # noqa: ANN401 - langchain Embeddings model
        """Build and cache the underlying model on first use."""
        if self._embeddings is None:
            try:
                self._embeddings = build_embeddings(
                    "huggingface", self._model_name, **self._kwargs
                )
            except LangChainResourceError as exc:
                raise EmbeddingProviderError(str(exc)) from exc
        return self._embeddings

    def warm_up(self) -> None:
        """Force the sentence-transformers model to load now, not on first embed.

        Builds the model and runs a single throwaway embedding so the (multi-GB,
        often GPU) weights are resident before the worker claims its first job.
        """
        try:
            self._get_embeddings().embed_documents(["warm up"])
        except EmbeddingProviderError:
            raise
        except Exception as exc:
            raise EmbeddingProviderError(
                f"HuggingFace model warm-up failed: {exc}"
            ) from exc

    def embed(
        self, texts: list[str], *, dimension: int, normalize: bool
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        try:
            vectors = self._get_embeddings().embed_documents(texts)

            # Truncate dimensions if the engine's model spec requests fewer than
            # the model produces; engine-side validation checks normalization.
            if dimension is not None:
                vectors = [v[:dimension] for v in vectors]

            return vectors
        except EmbeddingProviderError:
            raise
        except Exception as exc:
            raise EmbeddingProviderError(
                f"HuggingFace embedding generation failed: {exc}"
            ) from exc

"""Query embedding adapters for the vector worker (handbook Chapter 19.7).

The adapter abstracts embedding generation from the worker. The deterministic
``LocalHashEmbeddingAdapter`` keeps the vector path fully offline; the
``LangChainEmbeddingAdapter`` loads the embedding model EKIE used, through the
shared LangChain seam. The worker never chooses the model --- it is inherited.
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod

from domain.integrations import LangChainResourceError, build_embeddings
from domain.retrieval.errors import RetrievalWorkerError, RetrievalWorkerErrorType


class EmbeddingAdapter(ABC):
    """Generates a query embedding vector."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""

    @abstractmethod
    def embed(self, text: str) -> tuple[float, ...]:
        """Return the embedding vector for ``text``."""


class LocalHashEmbeddingAdapter(EmbeddingAdapter):
    """Deterministic, dependency-free hash embedder for the offline path."""

    def __init__(self, dimension: int = 256) -> None:
        if dimension <= 0:
            raise RetrievalWorkerError(
                RetrievalWorkerErrorType.EMBEDDING_FAILED,
                "embedding dimension must be positive",
            )
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        """Return the configured embedding dimension."""
        return self._dimension

    def embed(self, text: str) -> tuple[float, ...]:
        """Return a deterministic normalized vector derived from ``text``."""
        values: list[float] = []
        counter = 0
        while len(values) < self._dimension:
            digest = hashlib.sha256(f"{counter}:{text}".encode()).digest()
            for byte in digest:
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) >= self._dimension:
                    break
            counter += 1
        norm = math.sqrt(sum(v * v for v in values))
        if norm == 0.0:
            return tuple(values)
        return tuple(v / norm for v in values)


class LangChainEmbeddingAdapter(EmbeddingAdapter):
    """Embeds the query with the EKIE-inherited model via the LangChain seam."""

    def __init__(
        self, provider: str, model: str, *, dimension: int, base_url: str = ""
    ) -> None:
        self._provider = provider
        self._model = model
        self._dimension = dimension
        self._base_url = base_url
        self._embeddings: object | None = None

    @property
    def dimension(self) -> int:
        """Return the inherited embedding dimension."""
        return self._dimension

    def embed(self, text: str) -> tuple[float, ...]:
        """Return the query embedding, loading the model lazily on first use."""
        try:
            embeddings = self._load()
            vector = embeddings.embed_query(text)  # type: ignore[attr-defined]
        except LangChainResourceError as exc:
            raise RetrievalWorkerError(
                RetrievalWorkerErrorType.EMBEDDING_FAILED, str(exc)
            ) from exc
        except Exception as exc:  # noqa: BLE001 - external embedding boundary
            raise RetrievalWorkerError(
                RetrievalWorkerErrorType.EMBEDDING_FAILED,
                f"query embedding failed: {exc}",
            ) from exc
        return tuple(float(value) for value in vector)

    def _load(self) -> object:
        if self._embeddings is None:
            kwargs = {"base_url": self._base_url} if self._base_url else {}
            self._embeddings = build_embeddings(self._provider, self._model, **kwargs)
        return self._embeddings

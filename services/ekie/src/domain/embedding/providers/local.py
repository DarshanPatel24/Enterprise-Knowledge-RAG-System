"""Local, dependency-free deterministic embedding provider (local-first).

Generates reproducible pseudo-embeddings from content using SHA-256 expansion.
This keeps the ingestion pipeline fully self-hostable and testable without any
external embedding API, while conforming to the provider contract so a real
provider (Ollama, Sentence Transformers, Azure OpenAI, ...) can replace it
without framework changes (ADR-021).
"""

from __future__ import annotations

import hashlib
import math
import struct
from typing import ClassVar

from domain.embedding.providers.base import EmbeddingProvider, EmbeddingProviderError

_UINT32_MAX = 2**32


class LocalHashEmbeddingProvider(EmbeddingProvider):
    """Deterministic local embedding provider for offline, reproducible runs."""

    name: ClassVar[str] = "local"

    def embed(
        self, texts: list[str], *, dimension: int, normalize: bool
    ) -> list[list[float]]:
        """Return deterministic vectors of ``dimension`` floats per text."""
        if dimension <= 0:
            raise EmbeddingProviderError("dimension must be a positive integer")
        return [self._embed_one(text, dimension, normalize) for text in texts]

    @staticmethod
    def _embed_one(text: str, dimension: int, normalize: bool) -> list[float]:
        values: list[float] = []
        counter = 0
        seed = text or "\x00"
        while len(values) < dimension:
            digest = hashlib.sha256(f"{counter}:{seed}".encode()).digest()
            for offset in range(0, len(digest), 4):
                if len(values) >= dimension:
                    break
                (word,) = struct.unpack(">I", digest[offset : offset + 4])
                values.append((word / _UINT32_MAX) * 2.0 - 1.0)
            counter += 1
        if normalize:
            norm = math.sqrt(sum(value * value for value in values))
            if norm > 0.0:
                values = [value / norm for value in values]
        return values

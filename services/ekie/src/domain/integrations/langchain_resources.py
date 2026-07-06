"""LangChain resource template: one config-driven factory for the embedding
model and the vector store.

Consolidates LangChain initialization in a single place so engines and scripts
no longer each construct LangChain clients. Given model and vector-database
settings, it returns ready-to-use LangChain ``Embeddings`` and ``VectorStore``
objects --- the same building blocks used to build a RAG index. All third-party
imports are lazy, so the deterministic offline path never loads LangChain.

Note: the production publishing path deliberately keeps its own verified Qdrant
client (metadata gate, deterministic vector ids, read-back verification). This
template is the convenience/index seam and the single init point for the
HuggingFace and Ollama embedding models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_core.vectorstores import VectorStore
    from qdrant_client import QdrantClient

_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_DISTANCE_ALIASES = {"cosine": "Cosine", "dot_product": "Dot", "euclidean": "Euclid"}


class LangChainResourceError(RuntimeError):
    """Raised when a LangChain embedding model or vector store cannot be built."""


@dataclass(frozen=True)
class LangChainIndex:
    """A ready-to-use embedding model paired with its vector store."""

    embeddings: Embeddings
    vector_store: VectorStore


def build_embeddings(
    provider: str,
    model: str,
    *,
    base_url: str = _DEFAULT_OLLAMA_BASE_URL,
    **model_kwargs: Any,  # noqa: ANN401 - passthrough model kwargs
) -> Embeddings:
    """Build a LangChain embedding model for ``provider`` and ``model``.

    Supports ``huggingface`` (local sentence-transformers, cached under
    ``HF_HOME``) and ``ollama``. The deterministic ``local`` provider is not a
    LangChain model and is rejected here.
    """
    if provider == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError as exc:
            raise LangChainResourceError(
                "langchain-huggingface is not installed; install it to use "
                "HuggingFace embeddings"
            ) from exc
        return cast("Embeddings", HuggingFaceEmbeddings(model_name=model, **model_kwargs))
    if provider == "ollama":
        try:
            from langchain_ollama import OllamaEmbeddings
        except ImportError as exc:
            raise LangChainResourceError(
                "langchain-ollama is not installed; install it to use Ollama embeddings"
            ) from exc
        return cast("Embeddings", OllamaEmbeddings(model=model, base_url=base_url))
    raise LangChainResourceError(
        f"embedding provider {provider!r} is not a LangChain provider; use "
        f"'huggingface' or 'ollama' (the 'local' provider is deterministic and offline)"
    )


def build_qdrant_client(
    *,
    host: str = "localhost",
    port: int = 6333,
    url: str | None = None,
    api_key: str | None = None,
    location: str | None = None,
    timeout_seconds: float | None = None,
) -> QdrantClient:
    """Build a Qdrant client from one place, so connection init is centralized.

    Connection precedence: ``location`` (e.g. ``":memory:"``) > ``url`` >
    ``host``/``port``. This is the single factory used by both the production
    vector provider and the LangChain vector store.
    """
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise LangChainResourceError(
            "qdrant-client is required for the Qdrant connection"
        ) from exc
    timeout = int(timeout_seconds) if timeout_seconds else None
    if location is not None:
        return QdrantClient(location=location)
    if url:
        return QdrantClient(url=url, api_key=api_key or None, timeout=timeout)
    return QdrantClient(host=host, port=port, timeout=timeout)


def build_qdrant_vector_store(
    embeddings: Embeddings,
    *,
    collection: str,
    host: str = "localhost",
    port: int = 6333,
    url: str | None = None,
    api_key: str | None = None,
    location: str | None = None,
    distance: str = "cosine",
    vector_size: int | None = None,
    create_collection: bool = False,
    timeout_seconds: float | None = None,
) -> VectorStore:
    """Build a LangChain Qdrant vector store bound to ``collection``.

    Connection precedence: ``location`` (e.g. ``":memory:"``) > ``url`` >
    ``host``/``port``. When ``create_collection`` is set, the collection is
    created with ``vector_size`` if it does not already exist.
    """
    try:
        from langchain_qdrant import QdrantVectorStore
        from qdrant_client import models
    except ImportError as exc:
        raise LangChainResourceError(
            "langchain-qdrant and qdrant-client are required for the Qdrant vector store"
        ) from exc

    client = build_qdrant_client(
        host=host,
        port=port,
        url=url,
        api_key=api_key,
        location=location,
        timeout_seconds=timeout_seconds,
    )

    if create_collection:
        if vector_size is None or vector_size <= 0:
            raise LangChainResourceError(
                "vector_size is required to create a Qdrant collection"
            )
        if not client.collection_exists(collection):
            client.create_collection(
                collection,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance(_DISTANCE_ALIASES.get(distance, "Cosine")),
                ),
            )

    return cast(
        "VectorStore",
        QdrantVectorStore(
            client=client, collection_name=collection, embedding=embeddings
        ),
    )

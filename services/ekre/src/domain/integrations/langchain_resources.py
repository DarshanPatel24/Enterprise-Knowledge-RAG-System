"""LangChain resource template: one config-driven factory for the query
embedding model, the Qdrant vector store, and the retriever.

Consolidates LangChain initialization in a single place so the retrieval path
never constructs LangChain clients inline. Given the inherited embedding model
and the Qdrant connection, it returns ready-to-use LangChain ``Embeddings``, a
``VectorStore``, and a ``Retriever`` --- the building blocks the RAG retrieval
chain composes with (``retriever | format_candidates``). All third-party imports
are lazy so the deterministic offline path never loads LangChain.

The embedding model and distance metric are supplied by the inheritance
resolver (never hardcoded here); this module only wires the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

    from langchain_core.embeddings import Embeddings
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.runnables import Runnable
    from langchain_core.vectorstores import VectorStore

_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_DISTANCE_ALIASES = {"cosine": "Cosine", "dot_product": "Dot", "euclidean": "Euclid"}


class LangChainResourceError(RuntimeError):
    """Raised when a LangChain embedding model, store, or retriever cannot be built."""


class ChatModelLike(Protocol):
    """Minimal structural view of a LangChain chat model.

    Kept structural so engines can depend on the seam without importing a
    concrete LangChain model type on the offline path.
    """

    def invoke(self, input: Any, **kwargs: Any) -> Any: ...  # noqa: A002, ANN401


class CrossEncoderLike(Protocol):
    """Minimal structural view of a sentence-transformers cross-encoder reranker."""

    def predict(self, sentences: Any, **kwargs: Any) -> Any: ...  # noqa: ANN401


@dataclass(frozen=True)
class RetrievalResources:
    """A ready-to-use embedding model, vector store, and retriever."""

    embeddings: Embeddings
    vector_store: VectorStore
    retriever: BaseRetriever


def build_embeddings(
    provider: str,
    model: str,
    *,
    base_url: str = _DEFAULT_OLLAMA_BASE_URL,
    **model_kwargs: Any,  # noqa: ANN401 - passthrough model kwargs
) -> Embeddings:
    """Build a LangChain embedding model for ``provider`` and ``model``.

    Supports ``huggingface`` (local sentence-transformers, cached under
    ``HF_HOME``) and ``ollama``. The model must match the one EKIE used to
    produce the stored vectors; it is supplied by the inheritance resolver.
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
        f"embedding provider {provider!r} is not supported; use 'huggingface' or 'ollama'"
    )


def build_chat_model(
    provider: str,
    model: str,
    *,
    base_url: str = _DEFAULT_OLLAMA_BASE_URL,
    temperature: float = 0.0,
) -> ChatModelLike:
    """Build a LangChain chat model for ``provider`` and ``model``.

    The single provider-abstracted factory for chat models across EKRE (per the
    LangChain standards). Supports ``huggingface`` (local transformers pipeline)
    and ``ollama``; the provider and every parameter are supplied by the caller
    from settings so no runtime is hardcoded. Imports are lazy so the offline
    path never loads LangChain.
    """
    if provider == "huggingface":
        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
        except ImportError as exc:
            raise LangChainResourceError(
                "langchain-huggingface is not installed; install it to use a "
                "HuggingFace chat model"
            ) from exc
        pipeline = HuggingFacePipeline.from_model_id(
            model_id=model,
            task="text-generation",
            pipeline_kwargs={"temperature": temperature, "do_sample": temperature > 0.0},
        )
        return cast("ChatModelLike", ChatHuggingFace(llm=pipeline))
    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise LangChainResourceError(
                "langchain-ollama is not installed; install it to use an Ollama chat model"
            ) from exc
        return cast(
            "ChatModelLike",
            ChatOllama(model=model, base_url=base_url, temperature=temperature),
        )
    raise LangChainResourceError(
        f"chat model provider {provider!r} is not supported; use 'huggingface' or 'ollama'"
    )


def build_cross_encoder(
    model: str,
    *,
    device: str = "auto",
    torch_dtype: str = "auto",
    trust_remote_code: bool = False,
) -> CrossEncoderLike:
    """Build a sentence-transformers cross-encoder reranker model.

    A cross-encoder scores query/document relevance directly (no chat
    generation), the purpose-built way to rerank candidates. The model (for
    example ``Qwen/Qwen3-VL-Reranker-2B``) and device/precision come from
    settings, so no runtime is hardcoded. The import is lazy so the offline path
    never loads the model.
    """
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise LangChainResourceError(
            "sentence-transformers is not installed; install it to use the "
            "cross-encoder reranker"
        ) from exc
    kwargs: dict[str, Any] = {"trust_remote_code": trust_remote_code}
    if device and device != "auto":
        kwargs["device"] = device
    if torch_dtype and torch_dtype != "auto":
        kwargs["model_kwargs"] = {"torch_dtype": torch_dtype}
    return cast("CrossEncoderLike", CrossEncoder(model, **kwargs))


def build_qdrant_client(
    *,
    host: str = "localhost",
    port: int = 6333,
    url: str | None = None,
    api_key: str | None = None,
    location: str | None = None,
    timeout_seconds: float | None = None,
) -> Any:  # noqa: ANN401 - QdrantClient type is only available when installed
    """Build a Qdrant client from one place, so connection init is centralized.

    Connection precedence: ``location`` (e.g. ``":memory:"``) > ``url`` >
    ``host``/``port``.
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

    When ``create_collection`` is set, the collection is created with
    ``vector_size`` if it does not already exist. In the retrieval path the
    collection already exists (published by EKIE), so creation stays off.
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
        QdrantVectorStore(client=client, collection_name=collection, embedding=embeddings),
    )


def build_retriever(
    vector_store: VectorStore,
    *,
    search_type: str = "similarity",
    k: int = 5,
) -> BaseRetriever:
    """Build a retriever from a vector store (LCEL retrieval seam).

    Mirrors ``vector_store.as_retriever(search_type=..., search_kwargs={"k": k})``
    so the retriever composes directly in an LCEL chain via
    ``retriever | format_candidates``.
    """
    return cast(
        "BaseRetriever",
        vector_store.as_retriever(search_type=search_type, search_kwargs={"k": k}),
    )


def format_candidates(documents: Sequence[Any]) -> str:
    """Join retrieved document contents into a single context string.

    The chunk-merging helper used when composing the retrieval context; wrap it
    in ``RunnableLambda`` to use inside an LCEL chain.
    """
    return "\n\n".join(getattr(doc, "page_content", str(doc)) for doc in documents)


def build_format_candidates_runnable() -> Runnable[Any, str]:
    """Return ``format_candidates`` as an LCEL ``RunnableLambda``."""
    try:
        from langchain_core.runnables import RunnableLambda
    except ImportError as exc:
        raise LangChainResourceError(
            "langchain-core is required for the LCEL retrieval seam"
        ) from exc
    return cast("Runnable[Any, str]", RunnableLambda(format_candidates))

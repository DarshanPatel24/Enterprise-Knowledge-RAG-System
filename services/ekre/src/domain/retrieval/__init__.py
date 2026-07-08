"""Retrieval workers: vector, keyword, metadata + embedding + security filter."""

from domain.retrieval.embedding import (
    EmbeddingAdapter,
    LangChainEmbeddingAdapter,
    LocalHashEmbeddingAdapter,
)
from domain.retrieval.errors import (
    RetrievalWorkerError,
    RetrievalWorkerErrorType,
)
from domain.retrieval.factory import build_worker_registry
from domain.retrieval.normalize import to_candidates
from domain.retrieval.security import (
    enforce_clearance,
    enforce_tenant,
    resolve_allowed_clearances,
)
from domain.retrieval.workers import (
    KeywordRetrievalWorker,
    MetadataRetrievalWorker,
    VectorRetrievalWorker,
)

__all__ = [
    "EmbeddingAdapter",
    "KeywordRetrievalWorker",
    "LangChainEmbeddingAdapter",
    "LocalHashEmbeddingAdapter",
    "MetadataRetrievalWorker",
    "RetrievalWorkerError",
    "RetrievalWorkerErrorType",
    "VectorRetrievalWorker",
    "build_worker_registry",
    "enforce_clearance",
    "enforce_tenant",
    "resolve_allowed_clearances",
    "to_candidates",
]

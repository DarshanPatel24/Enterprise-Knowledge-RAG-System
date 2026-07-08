"""Worker registry factory: assemble the retrieval workers for a connector."""

from __future__ import annotations

from domain.connectors.base import RepositoryConnector
from domain.execution import WorkerRegistry
from domain.retrieval.embedding import EmbeddingAdapter
from domain.retrieval.workers import (
    KeywordRetrievalWorker,
    MetadataRetrievalWorker,
    VectorRetrievalWorker,
)


def build_worker_registry(
    connector: RepositoryConnector,
    adapter: EmbeddingAdapter,
    *,
    collection: str,
    require_security_context: bool = True,
    require_tenant_scope: bool = True,
) -> WorkerRegistry:
    """Register vector, keyword, and metadata workers for ``connector``."""
    registry = WorkerRegistry()
    registry.register(
        VectorRetrievalWorker(
            connector,
            adapter,
            collection=collection,
            require_security_context=require_security_context,
            require_tenant_scope=require_tenant_scope,
        )
    )
    registry.register(
        KeywordRetrievalWorker(
            connector,
            collection=collection,
            require_security_context=require_security_context,
            require_tenant_scope=require_tenant_scope,
        )
    )
    registry.register(
        MetadataRetrievalWorker(
            connector,
            collection=collection,
            require_security_context=require_security_context,
            require_tenant_scope=require_tenant_scope,
        )
    )
    return registry

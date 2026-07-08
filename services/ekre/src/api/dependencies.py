"""Shared FastAPI dependencies for the EKRE API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from config.settings import EkreSettings, get_settings
from domain.governance import RetrievalPipeline
from domain.ranking import Reranker
from domain.retrieval import EmbeddingAdapter


def get_app_settings() -> EkreSettings:
    """Return the process-wide EKRE settings."""
    return get_settings()


AppSettings = Annotated[EkreSettings, Depends(get_app_settings)]


# Process-wide singletons: the query embedding model (and the reranker inside the
# pipeline) load multi-GB weights, so they must be built once and reused across
# requests rather than rebuilt per call. Tests build via ``composition`` directly
# and never touch these, so they stay unaffected.
_query_embedding_adapter: EmbeddingAdapter | None = None
_reranker: Reranker | None = None
_retrieval_pipeline: RetrievalPipeline | None = None


def get_query_embedding_adapter() -> EmbeddingAdapter:
    """Return the process-wide query embedding adapter, building it on first use."""
    global _query_embedding_adapter
    if _query_embedding_adapter is None:
        from composition import build_query_embedding_adapter

        _query_embedding_adapter = build_query_embedding_adapter(get_settings())
    return _query_embedding_adapter


def get_reranker() -> Reranker:
    """Return the process-wide reranker, building it on first use.

    Shared with the pipeline so the cross-encoder model loads exactly once.
    """
    global _reranker
    if _reranker is None:
        from composition import build_reranker

        _reranker = build_reranker(get_settings())
    return _reranker


def get_retrieval_pipeline() -> RetrievalPipeline:
    """Return the process-wide retrieval pipeline, building it on first use.

    The pipeline shares the singleton embedding adapter and reranker so those
    models load exactly once for the whole process.
    """
    global _retrieval_pipeline
    if _retrieval_pipeline is None:
        from composition import build_retrieval_pipeline

        _retrieval_pipeline = build_retrieval_pipeline(
            get_settings(),
            adapter=get_query_embedding_adapter(),
            reranker=get_reranker(),
        )
    return _retrieval_pipeline


RetrievalPipelineDep = Annotated[RetrievalPipeline, Depends(get_retrieval_pipeline)]


def require_tenant(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> str:
    """Return the tenant id from the request header, or reject with 400."""
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required",
        )
    return x_tenant_id


TenantId = Annotated[str, Depends(require_tenant)]


def signed_security_context(
    x_security_context: Annotated[str | None, Header(alias="X-Security-Context")] = None,
) -> str | None:
    """Return the signed security-context token (JWT), if the caller supplied one."""
    return x_security_context


SignedSecurityContext = Annotated[str | None, Depends(signed_security_context)]

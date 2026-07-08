"""Retrieval configuration endpoint.

Exposes the resolved retrieval profile (embedding model, dimension, distance
metric) and the stage latency budgets. The profile is inherited from the EKIE
collection at request time; when the collection is unreachable the endpoint
reports the configured fallback and marks the source, proving that no embedding
model or distance metric is hardcoded in EKRE.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.dependencies import AppSettings, TenantId
from composition import build_inheritance_resolver
from domain.inheritance import InheritanceError
from domain.observability import get_logger

router = APIRouter(prefix="/v1/retrieval", tags=["retrieval"])
_logger = get_logger("ekre.api.retrieval")


class RetrievalConfigResponse(BaseModel):
    """Resolved retrieval configuration for a collection."""

    collection: str
    embedding_provider: str
    embedding_model: str
    dimension: int
    distance_metric: str
    source: str
    search_type: str
    default_top_k: int
    latency_budgets_ms: dict[str, float]


@router.get("/config", response_model=RetrievalConfigResponse)
async def retrieval_config(
    settings: AppSettings,
    tenant_id: TenantId,
    collection: str | None = None,
) -> RetrievalConfigResponse:
    """Return the retrieval configuration inherited from EKIE for a collection."""
    target = collection or settings.retrieval.default_collection
    if target not in settings.retrieval.allowed_collection_set():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="the requested collection is not permitted",
        )
    resolver = build_inheritance_resolver(settings)

    try:
        profile = resolver.resolve(target)
        embedding_model = profile.embedding_model
        dimension = profile.dimension
        distance_metric = profile.distance_metric.value
        source = profile.source
    except InheritanceError as exc:
        _logger.warning(
            "retrieval_config_inheritance_unavailable",
            extra={"collection": target, "error_type": exc.error_type.value},
        )
        embedding_model = settings.inheritance.fallback_embedding_model
        dimension = settings.inheritance.fallback_dimension
        distance_metric = settings.inheritance.fallback_distance_metric
        source = "fallback"

    return RetrievalConfigResponse(
        collection=target,
        embedding_provider=settings.embedding.provider,
        embedding_model=embedding_model,
        dimension=dimension,
        distance_metric=distance_metric,
        source=source,
        search_type=settings.retrieval.search_type,
        default_top_k=settings.retrieval.default_top_k,
        latency_budgets_ms=settings.retrieval.latency_budgets(),
    )

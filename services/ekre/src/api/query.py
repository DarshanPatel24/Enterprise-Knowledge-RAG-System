"""Query planning endpoint.

Accepts a raw query plus a security context, validates the context (the S0
pre-ranking gate), runs the deterministic query intelligence pipeline, and
returns the explainable Structured Query Model and Retrieval Execution Plan.
No retrieval is performed here (handbook: the Query Intelligence Domain plans
retrieval; it does not execute it).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import AppSettings, SignedSecurityContext, TenantId
from composition import (
    build_query_intelligence_engine,
    build_security_validator,
    record_access_denied,
)
from domain.observability import get_logger
from domain.query import QueryIntelligenceError, StructuredQuery
from domain.security import SecurityError

router = APIRouter(prefix="/v1/query", tags=["query"])
_logger = get_logger("ekre.api.query")


class SecurityContextPayload(BaseModel):
    """Security context supplied with a retrieval request."""

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    classification_clearance: str = Field(min_length=1)


class QueryPlanRequest(BaseModel):
    """Request body for query planning."""

    query: str = Field(min_length=1)
    security_context: SecurityContextPayload
    language: str | None = None


@router.post("/plan", response_model=StructuredQuery)
async def plan_query(
    request: QueryPlanRequest,
    settings: AppSettings,
    tenant_id: TenantId,
    signed_context: SignedSecurityContext,
) -> StructuredQuery:
    """Validate the security context and return the query intelligence plan."""
    validator = build_security_validator(settings)
    try:
        validator.validate(
            request.security_context.model_dump(),
            expected_tenant_id=tenant_id,
            signed_token=signed_context,
        )
    except SecurityError as exc:
        _logger.warning(
            "query_plan_security_rejected",
            extra={"error_type": exc.error_type.value},
        )
        record_access_denied(
            settings,
            actor=request.security_context.user_id,
            tenant_id=tenant_id,
            reason=exc.error_type.value,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    engine = build_query_intelligence_engine(settings)
    try:
        return engine.analyze(request.query, tenant_id=tenant_id, language=request.language)
    except QueryIntelligenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc

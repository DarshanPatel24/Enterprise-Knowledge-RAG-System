"""Query execution endpoint: plan + execute retrieval.

Validates the security context (the pre-ranking gate), runs the query
intelligence pipeline to build a plan, then executes it through the retrieval
orchestrator and returns the collected, clearance-filtered candidate session.
Ranking and context assembly are later sprints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import AppSettings, SignedSecurityContext, TenantId
from composition import (
    build_query_intelligence_engine,
    build_retrieval_orchestrator,
    build_security_validator,
    record_access_denied,
)
from domain.execution import ExecutionError, ExecutionSession
from domain.observability import get_logger
from domain.query import QueryIntelligenceError
from domain.security import SecurityContextValidator, SecurityError

router = APIRouter(prefix="/v1/query", tags=["query"])
_logger = get_logger("ekre.api.execute")


class SecurityContextPayload(BaseModel):
    """Security context supplied with a retrieval request."""

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    classification_clearance: str = Field(min_length=1)


class QueryExecuteRequest(BaseModel):
    """Request body for query execution."""

    query: str = Field(min_length=1)
    security_context: SecurityContextPayload
    language: str | None = None


@router.post("/execute", response_model=ExecutionSession)
async def execute_query(
    request: QueryExecuteRequest,
    settings: AppSettings,
    tenant_id: TenantId,
    signed_context: SignedSecurityContext,
) -> ExecutionSession:
    """Plan and execute retrieval, returning the collected candidate session."""
    validator: SecurityContextValidator = build_security_validator(settings)
    try:
        context = validator.validate(
            request.security_context.model_dump(),
            expected_tenant_id=tenant_id,
            signed_token=signed_context,
        )
    except SecurityError as exc:
        _logger.warning(
            "query_execute_security_rejected", extra={"error_type": exc.error_type.value}
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
    orchestrator = build_retrieval_orchestrator(settings)
    try:
        structured = engine.analyze(
            request.query, tenant_id=tenant_id, language=request.language
        )
        return orchestrator.execute(
            structured.plan,
            tenant_id=tenant_id,
            query=structured.understanding.normalized_query,
            metadata_filters=structured.understanding.metadata_filters,
            security_context=context,
        )
    except QueryIntelligenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc
    except ExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc

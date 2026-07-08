"""Full observable retrieval endpoint (handbook Chapters 28-29).

The production entry point: runs the complete EKRE pipeline with end-to-end
tracing, security auditing, and PII masking, and returns the traced result ---
the citation-preserving, masked handoff package plus the execution timeline.
Response generation is EKCP.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import AppSettings, SignedSecurityContext, TenantId
from composition import (
    build_retrieval_pipeline,
    build_security_validator,
    record_access_denied,
)
from domain.execution import ExecutionError
from domain.governance import TracedRetrieval
from domain.observability import get_logger
from domain.query import QueryIntelligenceError
from domain.security import SecurityContextValidator, SecurityError

router = APIRouter(prefix="/v1/query", tags=["query"])
_logger = get_logger("ekre.api.retrieve")


class SecurityContextPayload(BaseModel):
    """Security context supplied with a retrieval request."""

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    classification_clearance: str = Field(min_length=1)


class RetrieveRequest(BaseModel):
    """Request body for the full observable retrieval."""

    query: str = Field(min_length=1)
    security_context: SecurityContextPayload
    language: str | None = None


@router.post("/retrieve", response_model=TracedRetrieval)
async def retrieve(
    request: RetrieveRequest,
    settings: AppSettings,
    tenant_id: TenantId,
    signed_context: SignedSecurityContext,
) -> TracedRetrieval:
    """Run the full traced, audited, masked retrieval pipeline."""
    validator: SecurityContextValidator = build_security_validator(settings)
    try:
        context = validator.validate(
            request.security_context.model_dump(),
            expected_tenant_id=tenant_id,
            signed_token=signed_context,
        )
    except SecurityError as exc:
        _logger.warning("retrieve_security_rejected", extra={"error_type": exc.error_type.value})
        record_access_denied(
            settings,
            actor=request.security_context.user_id,
            tenant_id=tenant_id,
            reason=exc.error_type.value,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    if context is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="a security context is required"
        )

    pipeline = build_retrieval_pipeline(settings)
    try:
        return pipeline.retrieve(
            request.query,
            tenant_id=tenant_id,
            security_context=context,
            language=request.language,
        )
    except QueryIntelligenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc
    except ExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc

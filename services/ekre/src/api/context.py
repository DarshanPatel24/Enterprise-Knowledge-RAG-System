"""Context endpoint: the full EKRE pipeline through the EKCP handoff package.

Runs the complete pipeline --- query intelligence (S1), execution (S2/S3),
collection and fusion (S4), ranking (S5), and context assembly (S6) --- and
returns the assembled result: the citation-preserving Retrieval Context Package
handed to EKCP, plus auditable assembly metrics. Response generation is EKCP.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import AppSettings, SignedSecurityContext, TenantId
from composition import (
    build_candidate_collector,
    build_candidate_fusion,
    build_context_assembly_engine,
    build_query_intelligence_engine,
    build_ranking_engine,
    build_retrieval_orchestrator,
    build_security_validator,
    record_access_denied,
)
from domain.assembly import AssemblyResult
from domain.execution import ExecutionError
from domain.observability import get_logger
from domain.query import QueryIntelligenceError
from domain.security import SecurityContextValidator, SecurityError

router = APIRouter(prefix="/v1/query", tags=["query"])
_logger = get_logger("ekre.api.context")


class SecurityContextPayload(BaseModel):
    """Security context supplied with a retrieval request."""

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    classification_clearance: str = Field(min_length=1)


class ContextRequest(BaseModel):
    """Request body for assembled context retrieval."""

    query: str = Field(min_length=1)
    security_context: SecurityContextPayload
    language: str | None = None


@router.post("/context", response_model=AssemblyResult)
async def assemble_context(
    request: ContextRequest,
    settings: AppSettings,
    tenant_id: TenantId,
    signed_context: SignedSecurityContext,
) -> AssemblyResult:
    """Run the full pipeline and return the assembled EKCP handoff package."""
    validator: SecurityContextValidator = build_security_validator(settings)
    try:
        context = validator.validate(
            request.security_context.model_dump(),
            expected_tenant_id=tenant_id,
            signed_token=signed_context,
        )
    except SecurityError as exc:
        _logger.warning("context_security_rejected", extra={"error_type": exc.error_type.value})
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
    collector = build_candidate_collector()
    fusion = build_candidate_fusion(settings)
    ranking = build_ranking_engine(settings)
    assembly = build_context_assembly_engine(settings)
    try:
        structured = engine.analyze(
            request.query, tenant_id=tenant_id, language=request.language
        )
        session = orchestrator.execute(
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

    unified = collector.collect(session.outcomes)
    fused = fusion.fuse(unified)
    ranked = ranking.rank(fused, query=structured.understanding.normalized_query)
    return assembly.assemble(
        ranked,
        query=structured.understanding.normalized_query,
        tenant_id=tenant_id,
        security_filtered=True,
    )

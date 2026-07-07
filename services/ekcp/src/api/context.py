"""Context orchestration API: build the Execution Context Package."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId
from contracts.retrieval import (
    Citation,
    RetrievalCandidate,
    RetrievalContextPackage,
)
from domain.context import ContextItem, ContextSource
from domain.observability import get_logger
from domain.security import SecurityError

router = APIRouter(prefix="/context", tags=["context"])

logger = get_logger("ekcp.api.context")


class SecurityContextPayload(BaseModel):
    """Security context carried on a context request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class CitationPayload(BaseModel):
    """Citation lineage for a supplied knowledge candidate."""

    document_id: str
    chunk_id: str
    source_path: str


class KnowledgeCandidatePayload(BaseModel):
    """A retrieval candidate supplied inline (live EKRE fetch lands in EKCP-S7)."""

    content: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    citation: CitationPayload
    explanation: str | None = None


class BuildContextRequest(BaseModel):
    """Request body to assemble an Execution Context Package."""

    conversation_id: str
    user_intent: str = Field(min_length=1)
    security_context: SecurityContextPayload
    conversation_history: list[str] = Field(default_factory=list)
    knowledge: list[KnowledgeCandidatePayload] = Field(default_factory=list)
    policy_constraints: list[str] = Field(default_factory=list)


class BuildContextResponse(BaseModel):
    """Response for an assembled context package."""

    context_id: str
    conversation_id: str
    selected_count: int
    total_tokens: int
    source_diversity: int
    compression_applied: bool
    warnings: list[str]


def _validate_security(
    resources: Resources, payload: SecurityContextPayload, tenant_id: str
) -> None:
    try:
        resources.security_validator.validate(
            payload.model_dump(), expected_tenant_id=tenant_id
        )
    except SecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc


@router.post("/build", response_model=BuildContextResponse)
async def build_context(
    request: BuildContextRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> BuildContextResponse:
    """Assemble and persist the Execution Context Package for a conversation turn."""
    _validate_security(resources, request.security_context, tenant_id)

    retrieval: RetrievalContextPackage | None = None
    if request.knowledge:
        retrieval = RetrievalContextPackage(
            query=request.user_intent,
            tenant_id=tenant_id,
            candidates=[
                RetrievalCandidate(
                    citation=Citation(
                        document_id=candidate.citation.document_id,
                        chunk_id=candidate.citation.chunk_id,
                        source_path=candidate.citation.source_path,
                    ),
                    content=candidate.content,
                    relevance_score=candidate.relevance_score,
                    explanation=candidate.explanation,
                )
                for candidate in request.knowledge
            ],
        )

    policy_items = tuple(
        ContextItem(
            source=ContextSource.POLICY,
            content=constraint,
            reason="policy constraint",
            rank_score=1.0,
        )
        for constraint in request.policy_constraints
        if constraint.strip()
    )

    package = resources.context_assembler.assemble(
        tenant_id=tenant_id,
        conversation_id=request.conversation_id,
        user_intent=request.user_intent,
        conversation_history=tuple(request.conversation_history),
        retrieval=retrieval,
        policy_items=policy_items,
    )
    resources.context_store.save(package)
    logger.info(
        "context_built",
        extra={
            "context_id": package.context_id,
            "conversation_id": request.conversation_id,
        },
    )
    return BuildContextResponse(
        context_id=package.context_id,
        conversation_id=package.conversation_id,
        selected_count=package.metrics.selected_count,
        total_tokens=package.metrics.total_tokens,
        source_diversity=package.metrics.source_diversity,
        compression_applied=package.compression_applied,
        warnings=list(package.warnings),
    )

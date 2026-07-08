"""Memory API: store, retrieve, consolidate, and forget governed memory."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId, build_principal
from domain.governance import GovernanceError, Permission
from domain.memory import (
    CompressionLevel,
    MemoryError,
    MemoryErrorType,
    MemoryScope,
    MemoryType,
    ValidationMethod,
)
from domain.observability import get_logger
from domain.security import SecurityError

router = APIRouter(prefix="/memory", tags=["memory"])

logger = get_logger("ekcp.api.memory")


class SecurityContextPayload(BaseModel):
    """Security context carried on a memory request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class StoreMemoryRequest(BaseModel):
    """Request body to store a memory item."""

    security_context: SecurityContextPayload
    content: str = Field(min_length=1, max_length=16000)
    memory_type: MemoryType = MemoryType.FACT
    scope: MemoryScope = MemoryScope.CONVERSATION
    validation_method: ValidationMethod = ValidationMethod.USER_CONFIRMED
    topic: str = ""
    tags: list[str] = Field(default_factory=list)
    conversation_id: str | None = None
    user_id: str | None = None


class StoreMemoryResponse(BaseModel):
    """Response for a stored memory item."""

    memory_id: str
    scope: str
    confidence: float
    expires_at: str | None


class RetrieveMemoryRequest(BaseModel):
    """Request body to retrieve ranked memories."""

    security_context: SecurityContextPayload
    query: str = Field(min_length=1)
    scopes: list[MemoryScope] | None = None
    limit: int | None = None
    min_confidence: float | None = None


class MemoryHit(BaseModel):
    """A single ranked memory result."""

    memory_id: str
    content: str
    scope: str
    memory_type: str
    score: float
    confidence: float


class RetrieveMemoryResponse(BaseModel):
    """Response for a memory retrieval."""

    hits: list[MemoryHit]


class ConsolidateMemoryRequest(BaseModel):
    """Request body to consolidate a conversation's memories."""

    security_context: SecurityContextPayload
    conversation_id: str
    level: CompressionLevel = CompressionLevel.SUMMARY


class ConsolidateMemoryResponse(BaseModel):
    """Response for a memory consolidation."""

    memory_id: str
    content: str
    source_count: int


class PurgeMemoryRequest(BaseModel):
    """Request body to purge memories for a user or conversation."""

    security_context: SecurityContextPayload
    user_id: str | None = None
    conversation_id: str | None = None
    reason: str = "user_request"


class PurgeMemoryResponse(BaseModel):
    """Response for a memory purge."""

    deleted_count: int


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


def _authorize(
    resources: Resources,
    payload: SecurityContextPayload,
    tenant_id: str,
    permission: Permission,
    resource: str,
) -> None:
    _validate_security(resources, payload, tenant_id)
    principal = build_principal(
        resources,
        user_id=payload.user_id,
        tenant_id=tenant_id,
        clearance=payload.classification_clearance,
    )
    try:
        resources.governance_guard.authorize(principal, permission, resource)
    except GovernanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc


@router.post("/store", response_model=StoreMemoryResponse)
async def store_memory(
    request: StoreMemoryRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> StoreMemoryResponse:
    """Store a governed memory item."""
    _authorize(
        resources, request.security_context, tenant_id, Permission.WRITE_MEMORY, "memory"
    )
    content, _ = resources.governance_guard.sanitize_input(
        request.content,
        actor=request.security_context.user_id,
        tenant_id=tenant_id,
        resource="memory",
    )
    item = resources.memory_framework.remember(
        tenant_id=tenant_id,
        content=content,
        memory_type=request.memory_type,
        scope=request.scope,
        validation_method=request.validation_method,
        topic=request.topic,
        tags=tuple(request.tags),
        conversation_id=request.conversation_id,
        user_id=request.user_id or request.security_context.user_id,
    )
    return StoreMemoryResponse(
        memory_id=item.memory_id,
        scope=item.scope,
        confidence=item.confidence,
        expires_at=item.expires_at.isoformat() if item.expires_at else None,
    )


@router.post("/retrieve", response_model=RetrieveMemoryResponse)
async def retrieve_memory(
    request: RetrieveMemoryRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> RetrieveMemoryResponse:
    """Retrieve ranked memories for a query."""
    _authorize(
        resources, request.security_context, tenant_id, Permission.READ_MEMORY, "memory"
    )
    scored = resources.memory_framework.recall(
        tenant_id=tenant_id,
        query=request.query,
        scopes=request.scopes,
        limit=request.limit,
        min_confidence=request.min_confidence,
    )
    return RetrieveMemoryResponse(
        hits=[
            MemoryHit(
                memory_id=entry.item.memory_id,
                content=entry.item.content,
                scope=entry.item.scope,
                memory_type=entry.item.memory_type,
                score=entry.score,
                confidence=entry.item.confidence,
            )
            for entry in scored
        ]
    )


@router.post("/consolidate", response_model=ConsolidateMemoryResponse)
async def consolidate_memory(
    request: ConsolidateMemoryRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> ConsolidateMemoryResponse:
    """Consolidate a conversation's active memories into a long-term summary."""
    _authorize(
        resources, request.security_context, tenant_id, Permission.WRITE_MEMORY, "memory"
    )
    try:
        item = resources.memory_framework.consolidate(
            tenant_id=tenant_id,
            conversation_id=request.conversation_id,
            level=request.level,
        )
    except MemoryError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if exc.error_type is MemoryErrorType.NOTHING_TO_CONSOLIDATE
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=exc.message) from exc
    return ConsolidateMemoryResponse(
        memory_id=item.memory_id,
        content=item.content,
        source_count=len(item.related_memories),
    )


@router.post("/purge", response_model=PurgeMemoryResponse)
async def purge_memory(
    request: PurgeMemoryRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> PurgeMemoryResponse:
    """Hard-delete memories for a user or conversation (right-to-be-forgotten)."""
    _authorize(
        resources, request.security_context, tenant_id, Permission.WRITE_MEMORY, "memory"
    )
    deleted = resources.memory_framework.forget(
        tenant_id=tenant_id,
        user_id=request.user_id,
        conversation_id=request.conversation_id,
    )
    logger.info("memory_purged", extra={"deleted": deleted, "reason": request.reason})
    return PurgeMemoryResponse(deleted_count=deleted)

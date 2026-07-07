"""Governance API: evaluate a policy decision and retrieve the audit trail."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId, build_principal
from domain.governance import (
    AccessRequest,
    GovernanceError,
    InMemoryAuditSink,
    Permission,
    parse_clearance,
)
from domain.observability import get_logger
from domain.security import SecurityError

router = APIRouter(prefix="/governance", tags=["governance"])

logger = get_logger("ekcp.api.governance")


class SecurityContextPayload(BaseModel):
    """Security context carried on a governance request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class EvaluatePolicyRequest(BaseModel):
    """Request body to evaluate a policy decision for an operation."""

    security_context: SecurityContextPayload
    permission: str
    resource: str
    resource_classification: str = "internal"
    roles: list[str] = Field(default_factory=list)


class EvaluatePolicyResponse(BaseModel):
    """Response for a policy evaluation."""

    allowed: bool
    reason: str
    policy_version: str


class AuditRecordResponse(BaseModel):
    """A single audit trail entry."""

    event_id: str
    action: str
    result: str
    actor: str
    resource: str
    reason: str


class AuditHistoryResponse(BaseModel):
    """Response for an audit trail query."""

    records: list[AuditRecordResponse]
    total: int


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


@router.post("/evaluate", response_model=EvaluatePolicyResponse)
async def evaluate_policy(
    request: EvaluatePolicyRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> EvaluatePolicyResponse:
    """Evaluate (without executing) a policy decision for a governed operation."""
    _validate_security(resources, request.security_context, tenant_id)
    try:
        permission = Permission(request.permission)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"unknown permission {request.permission!r}",
        ) from exc

    principal = build_principal(
        resources,
        user_id=request.security_context.user_id,
        tenant_id=tenant_id,
        clearance=request.security_context.classification_clearance,
        roles=request.roles,
    )
    try:
        resource_clearance = parse_clearance(request.resource_classification)
    except GovernanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc

    decision = resources.governance_guard.evaluate(
        AccessRequest(
            principal=principal,
            permission=permission,
            resource=request.resource,
            resource_classification=resource_clearance,
        )
    )
    return EvaluatePolicyResponse(
        allowed=decision.allowed,
        reason=decision.reason,
        policy_version=decision.policy_version,
    )


@router.get("/audit", response_model=AuditHistoryResponse)
async def audit_history(
    tenant_id: TenantId,
    resources: Resources,
) -> AuditHistoryResponse:
    """Return the audit trail for the tenant (in-memory sink only)."""
    sink = resources.governance_guard.audit_sink
    if not isinstance(sink, InMemoryAuditSink):
        return AuditHistoryResponse(records=[], total=0)
    records = sink.history(tenant_id=tenant_id)
    return AuditHistoryResponse(
        records=[
            AuditRecordResponse(
                event_id=record.event_id,
                action=record.action,
                result=record.result,
                actor=record.actor,
                resource=record.resource,
                reason=record.reason,
            )
            for record in records
        ],
        total=len(records),
    )

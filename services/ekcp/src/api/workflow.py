"""Workflow API: trigger, inspect, pause, resume, and approve workflows."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId
from domain.observability import get_logger
from domain.security import SecurityError
from domain.workflow import Workflow, WorkflowError, WorkflowErrorType

router = APIRouter(prefix="/workflow", tags=["workflow"])

logger = get_logger("ekcp.api.workflow")


class SecurityContextPayload(BaseModel):
    """Security context carried on a workflow request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class TriggerWorkflowRequest(BaseModel):
    """Request body to trigger a workflow."""

    security_context: SecurityContextPayload
    objective: str = Field(min_length=1, max_length=16000)


class WorkflowActionRequest(BaseModel):
    """Request body for a workflow lifecycle action (pause/resume/approve)."""

    security_context: SecurityContextPayload


class WorkflowResponse(BaseModel):
    """Response describing a workflow's current state."""

    workflow_id: str
    state: str
    plan_id: str | None
    task_count: int
    version_number: int


_WORKFLOW_STATUS = {
    WorkflowErrorType.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    WorkflowErrorType.INVALID_TRANSITION: status.HTTP_409_CONFLICT,
    WorkflowErrorType.INVALID_STATE: status.HTTP_409_CONFLICT,
}


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


def _to_response(workflow: Workflow) -> WorkflowResponse:
    return WorkflowResponse(
        workflow_id=workflow.workflow_id,
        state=workflow.state,
        plan_id=workflow.plan_id,
        task_count=workflow.task_count,
        version_number=workflow.version_number,
    )


def _handle(action: str, workflow_getter: Callable[[], Workflow]) -> Workflow:
    try:
        return workflow_getter()
    except WorkflowError as exc:
        raise HTTPException(
            status_code=_WORKFLOW_STATUS.get(
                exc.error_type, status.HTTP_400_BAD_REQUEST
            ),
            detail=exc.message,
        ) from exc


@router.post("/trigger", response_model=WorkflowResponse)
async def trigger_workflow(
    request: TriggerWorkflowRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> WorkflowResponse:
    """Trigger a workflow and generate its execution plan."""
    _validate_security(resources, request.security_context, tenant_id)
    workflow = resources.workflow_orchestrator.trigger(
        tenant_id=tenant_id, objective=request.objective
    )
    logger.info("workflow_triggered", extra={"workflow_id": workflow.workflow_id})
    return _to_response(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    tenant_id: TenantId,
    resources: Resources,
) -> WorkflowResponse:
    """Return the current state of a workflow."""
    workflow = _handle(
        "get", lambda: resources.workflow_orchestrator.get(tenant_id, workflow_id)
    )
    return _to_response(workflow)


@router.post("/{workflow_id}/pause", response_model=WorkflowResponse)
async def pause_workflow(
    workflow_id: str,
    request: WorkflowActionRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> WorkflowResponse:
    """Pause an active workflow."""
    _validate_security(resources, request.security_context, tenant_id)
    workflow = _handle(
        "pause", lambda: resources.workflow_orchestrator.pause(tenant_id, workflow_id)
    )
    return _to_response(workflow)


@router.post("/{workflow_id}/resume", response_model=WorkflowResponse)
async def resume_workflow(
    workflow_id: str,
    request: WorkflowActionRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> WorkflowResponse:
    """Resume a paused workflow."""
    _validate_security(resources, request.security_context, tenant_id)
    workflow = _handle(
        "resume", lambda: resources.workflow_orchestrator.resume(tenant_id, workflow_id)
    )
    return _to_response(workflow)


@router.post("/{workflow_id}/approve", response_model=WorkflowResponse)
async def approve_workflow(
    workflow_id: str,
    request: WorkflowActionRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> WorkflowResponse:
    """Record a human approval for a waiting or paused workflow."""
    _validate_security(resources, request.security_context, tenant_id)
    workflow = _handle(
        "approve", lambda: resources.workflow_orchestrator.approve(tenant_id, workflow_id)
    )
    return _to_response(workflow)

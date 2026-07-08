"""Agent runtime API: execute an agent and plan an objective."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId, build_principal
from domain.agents import AgentError, AgentErrorType, AgentRequest, Capability
from domain.governance import GovernanceError, Permission
from domain.observability import get_correlation_id, get_logger
from domain.planning import PlanningError, PlanningErrorType
from domain.security import SecurityError

router = APIRouter(prefix="/agent", tags=["agent"])

logger = get_logger("ekcp.api.agent")


class SecurityContextPayload(BaseModel):
    """Security context carried on an agent request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class ExecuteAgentRequest(BaseModel):
    """Request body to execute an agent for a capability."""

    security_context: SecurityContextPayload
    task_description: str = Field(min_length=1, max_length=16000)
    capability: str
    prompt_text: str | None = Field(default=None, max_length=200000)
    granted_permissions: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)


class ToolUsageResponse(BaseModel):
    """A single tool invocation summary."""

    tool_id: str
    status: str
    duration_ms: float


class ExecuteAgentResponse(BaseModel):
    """Response for an agent execution."""

    agent_id: str
    status: str
    result: str
    confidence_score: float
    model_used: str
    steps: int
    tool_usage: list[ToolUsageResponse]
    recommended_next_actions: list[str]


class PlanRequest(BaseModel):
    """Request body to plan an objective."""

    security_context: SecurityContextPayload
    objective: str = Field(min_length=1, max_length=16000)


class PlanTaskResponse(BaseModel):
    """A single planned task."""

    task_id: str
    description: str
    required_capability: str
    dependencies: list[str]
    approval_required: bool
    priority: int


class PlanResponse(BaseModel):
    """Response for a planned objective."""

    plan_id: str
    objective: str
    execution_strategy: str
    tasks: list[PlanTaskResponse]
    approval_checkpoints: list[str]


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


@router.post("/execute", response_model=ExecuteAgentResponse)
async def execute_agent_endpoint(
    request: ExecuteAgentRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> ExecuteAgentResponse:
    """Select an agent by capability and execute it through the runtime."""
    _validate_security(resources, request.security_context, tenant_id)

    principal = build_principal(
        resources,
        user_id=request.security_context.user_id,
        tenant_id=tenant_id,
        clearance=request.security_context.classification_clearance,
        roles=request.roles,
    )
    try:
        resources.governance_guard.authorize(
            principal, Permission.INVOKE_AGENT, request.capability
        )
    except GovernanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    try:
        capability = Capability(request.capability)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"unknown capability {request.capability!r}",
        ) from exc

    granted = frozenset(request.granted_permissions)
    try:
        descriptor = resources.agent_selector.select(
            resources.agent_registry, capability, granted_permissions=granted
        )
    except AgentError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if exc.error_type is AgentErrorType.NO_AGENT_FOUND
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=exc.message) from exc

    outcome = resources.agent_runtime.run(
        descriptor,
        AgentRequest(
            task_description=request.task_description,
            capability=capability,
            tenant_id=tenant_id,
            prompt_text=request.prompt_text,
            user_identity=request.security_context.user_id,
            correlation_id=get_correlation_id(),
            granted_permissions=granted,
        ),
        gateway=resources.model_gateway,
        tool_executor=resources.tool_executor,
        policy=resources.agent_policy,
    )
    masked_result, _ = resources.governance_guard.mask_response(
        outcome.result,
        actor=principal.user_id,
        tenant_id=tenant_id,
        resource=descriptor.agent_id,
    )
    logger.info(
        "agent_execute", extra={"agent_id": outcome.agent_id, "status": outcome.status}
    )
    return ExecuteAgentResponse(
        agent_id=outcome.agent_id,
        status=outcome.status,
        result=masked_result,
        confidence_score=outcome.confidence_score,
        model_used=outcome.model_used,
        steps=outcome.steps,
        tool_usage=[
            ToolUsageResponse(
                tool_id=usage.tool_id, status=usage.status, duration_ms=usage.duration_ms
            )
            for usage in outcome.tool_usage
        ],
        recommended_next_actions=list(outcome.recommended_next_actions),
    )


@router.post("/plan", response_model=PlanResponse)
async def plan_endpoint(
    request: PlanRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> PlanResponse:
    """Decompose an objective into an ordered execution plan."""
    _validate_security(resources, request.security_context, tenant_id)
    try:
        plan = resources.planning_engine.plan(request.objective)
    except PlanningError as exc:
        code = (
            status.HTTP_422_UNPROCESSABLE_CONTENT
            if exc.error_type is PlanningErrorType.EMPTY_OBJECTIVE
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=exc.message) from exc
    return PlanResponse(
        plan_id=plan.plan_id,
        objective=plan.objective,
        execution_strategy=plan.execution_strategy,
        tasks=[
            PlanTaskResponse(
                task_id=task.task_id,
                description=task.description,
                required_capability=task.required_capability,
                dependencies=list(task.dependencies),
                approval_required=task.approval_required,
                priority=task.priority,
            )
            for task in plan.tasks
        ],
        approval_checkpoints=[cp.checkpoint_id for cp in plan.approval_checkpoints],
    )

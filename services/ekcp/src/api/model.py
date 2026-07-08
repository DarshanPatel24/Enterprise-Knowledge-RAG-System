"""Model gateway API: invoke a model through the governed gateway."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId, build_principal
from domain.context import ContextError, ContextErrorType
from domain.gateway import GatewayError, GatewayErrorType, GenerationRequest, ResponseType
from domain.governance import GovernanceError, Permission
from domain.observability import get_correlation_id, get_logger
from domain.prompt import PromptError
from domain.security import SecurityError

router = APIRouter(prefix="/model", tags=["model"])

logger = get_logger("ekcp.api.model")


class SecurityContextPayload(BaseModel):
    """Security context carried on a model request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class InvokeModelRequest(BaseModel):
    """Request body to invoke a model.

    Supply either an assembled ``prompt_text`` or a ``context_id`` from a prior
    ``/context/build`` call (the prompt is then constructed from that context).
    """

    security_context: SecurityContextPayload
    prompt_text: str | None = Field(default=None, max_length=200000)
    context_id: str | None = None
    template_id: str | None = None
    model_id: str | None = None
    response_type: str = "markdown"
    conversation_id: str | None = None


class TokenUsageResponse(BaseModel):
    """Token accounting for an invocation."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class InvokeModelResponse(BaseModel):
    """Response for a model invocation."""

    model_id: str
    provider: str
    output: str
    response_type: str
    token_usage: TokenUsageResponse
    latency_ms: float
    cost_estimate: float
    fallback_used: bool


_GATEWAY_STATUS = {
    GatewayErrorType.UNKNOWN_MODEL: status.HTTP_404_NOT_FOUND,
    GatewayErrorType.MODEL_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    GatewayErrorType.NOT_APPROVED: status.HTTP_409_CONFLICT,
    GatewayErrorType.PROVIDER_FAILED: status.HTTP_502_BAD_GATEWAY,
    GatewayErrorType.FALLBACK_EXHAUSTED: status.HTTP_502_BAD_GATEWAY,
    GatewayErrorType.TOKEN_LIMIT_EXCEEDED: status.HTTP_413_CONTENT_TOO_LARGE,
    GatewayErrorType.BUDGET_EXCEEDED: status.HTTP_402_PAYMENT_REQUIRED,
}


def _resolve_prompt(resources: Resources, request: InvokeModelRequest, tenant_id: str) -> str:
    if request.prompt_text and request.prompt_text.strip():
        return request.prompt_text
    if not request.context_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="either prompt_text or context_id is required",
        )
    try:
        ecp = resources.context_store.get(tenant_id, request.context_id)
    except ContextError as exc:
        code = (
            status.HTTP_404_NOT_FOUND
            if exc.error_type is ContextErrorType.NOT_FOUND
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=exc.message) from exc
    try:
        package = resources.prompt_orchestrator.build(ecp, template_id=request.template_id)
    except PromptError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc
    return package.prompt_text


@router.post("/invoke", response_model=InvokeModelResponse)
async def invoke_model(
    request: InvokeModelRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> InvokeModelResponse:
    """Invoke a model through the governed gateway and return the normalized response."""
    try:
        resources.security_validator.validate(
            request.security_context.model_dump(), expected_tenant_id=tenant_id
        )
    except SecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    principal = build_principal(
        resources,
        user_id=request.security_context.user_id,
        tenant_id=tenant_id,
        clearance=request.security_context.classification_clearance,
    )
    try:
        resources.governance_guard.authorize(
            principal, Permission.GENERATE_RESPONSE, request.model_id or "model"
        )
    except GovernanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    prompt_text = _resolve_prompt(resources, request, tenant_id)
    generation = GenerationRequest(
        prompt_text=prompt_text,
        tenant_id=tenant_id,
        model_id=request.model_id,
        conversation_id=request.conversation_id,
        correlation_id=get_correlation_id(),
    )
    generation = generation.model_copy(
        update={
            "constraints": generation.constraints.model_copy(
                update={"response_type": ResponseType(request.response_type)}
            )
        }
    )

    try:
        response = resources.model_gateway.invoke(generation)
    except GatewayError as exc:
        raise HTTPException(
            status_code=_GATEWAY_STATUS.get(exc.error_type, status.HTTP_400_BAD_REQUEST),
            detail=exc.message,
        ) from exc

    logger.info("model_invoked", extra={"model_id": response.model_id})
    masked_output, _ = resources.governance_guard.mask_response(
        response.output_text,
        actor=principal.user_id,
        tenant_id=tenant_id,
        resource=response.model_id,
    )
    return InvokeModelResponse(
        model_id=response.model_id,
        provider=response.provider,
        output=masked_output,
        response_type=response.response_type,
        token_usage=TokenUsageResponse(
            prompt_tokens=response.token_usage.prompt_tokens,
            completion_tokens=response.token_usage.completion_tokens,
            total_tokens=response.token_usage.total_tokens,
        ),
        latency_ms=response.latency_ms,
        cost_estimate=response.cost_estimate,
        fallback_used=response.fallback_used,
    )

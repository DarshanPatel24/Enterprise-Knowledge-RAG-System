"""Prompt orchestration API: generate a governed Prompt Package from context."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.dependencies import Resources, TenantId
from domain.context import ContextError, ContextErrorType
from domain.observability import get_logger
from domain.prompt import PromptError, PromptErrorType
from domain.security import SecurityError

router = APIRouter(prefix="/prompt", tags=["prompt"])

logger = get_logger("ekcp.api.prompt")


class SecurityContextPayload(BaseModel):
    """Security context carried on a prompt request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class GeneratePromptRequest(BaseModel):
    """Request body to generate a prompt package for a built context."""

    context_id: str
    security_context: SecurityContextPayload
    template_id: str | None = None
    output_format: str | None = None


class GeneratePromptResponse(BaseModel):
    """Response for a generated prompt package."""

    prompt_id: str
    prompt_text: str
    template_id: str
    template_version: str
    token_estimate: int
    validation_status: str
    compression_applied: bool


_PROMPT_STATUS = {
    PromptErrorType.UNKNOWN_TEMPLATE: status.HTTP_404_NOT_FOUND,
    PromptErrorType.MISSING_VARIABLE: status.HTTP_422_UNPROCESSABLE_CONTENT,
    PromptErrorType.POLICY_CONFLICT: status.HTTP_409_CONFLICT,
}


@router.post("/generate", response_model=GeneratePromptResponse)
async def generate_prompt(
    request: GeneratePromptRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> GeneratePromptResponse:
    """Generate a validated prompt package from a previously built context."""
    try:
        resources.security_validator.validate(
            request.security_context.model_dump(), expected_tenant_id=tenant_id
        )
    except SecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

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
        package = resources.prompt_orchestrator.build(
            ecp, template_id=request.template_id, output_format=request.output_format
        )
    except PromptError as exc:
        raise HTTPException(
            status_code=_PROMPT_STATUS.get(exc.error_type, status.HTTP_400_BAD_REQUEST),
            detail=exc.message,
        ) from exc

    logger.info("prompt_built", extra={"prompt_id": package.prompt_id})
    return GeneratePromptResponse(
        prompt_id=package.prompt_id,
        prompt_text=package.prompt_text,
        template_id=package.template_id,
        template_version=package.template_version,
        token_estimate=package.token_estimate,
        validation_status=package.validation_status,
        compression_applied=package.compression_applied,
    )

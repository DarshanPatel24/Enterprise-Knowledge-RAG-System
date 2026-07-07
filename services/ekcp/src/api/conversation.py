"""Conversation core API: start a conversation and add governed interactions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId
from domain.conversation import ConversationError, ConversationErrorType
from domain.intent import IntentError
from domain.observability import get_logger
from domain.security import SecurityError
from domain.session import SessionError, SessionErrorType

router = APIRouter(prefix="/conversation", tags=["conversation"])

logger = get_logger("ekcp.api.conversation")


class SecurityContextPayload(BaseModel):
    """Security context carried on a conversation request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class StartConversationRequest(BaseModel):
    """Request body to start a new conversation."""

    security_context: SecurityContextPayload
    title: str = "New Conversation"
    workspace_id: str | None = None
    participants: list[str] = Field(default_factory=list)


class StartConversationResponse(BaseModel):
    """Response for a newly started conversation."""

    conversation_id: str
    session_id: str
    state: str


class MessageRequest(BaseModel):
    """Request body to add a user message to a conversation."""

    conversation_id: str
    session_id: str
    message: str = Field(min_length=1)
    security_context: SecurityContextPayload


class MessageResponse(BaseModel):
    """Response for a handled interaction."""

    interaction_id: str
    conversation_state: str
    intent: str
    scope: str
    confidence: float
    requires_clarification: bool
    clarification_prompt: str
    routing_target: str
    assistant_response: str


_CONVERSATION_STATUS = {
    ConversationErrorType.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ConversationErrorType.INVALID_STATE: status.HTTP_409_CONFLICT,
    ConversationErrorType.INVALID_TRANSITION: status.HTTP_409_CONFLICT,
    ConversationErrorType.VERSION_CONFLICT: status.HTTP_409_CONFLICT,
    ConversationErrorType.EMPTY_MESSAGE: status.HTTP_422_UNPROCESSABLE_CONTENT,
}

_SESSION_STATUS = {
    SessionErrorType.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    SessionErrorType.EXPIRED: status.HTTP_401_UNAUTHORIZED,
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


@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(
    request: StartConversationRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> StartConversationResponse:
    """Start a new conversation and open a session for the owner."""
    _validate_security(resources, request.security_context, tenant_id)
    owner_id = request.security_context.user_id

    session = resources.session_manager.create(tenant_id=tenant_id, user_id=owner_id)
    conversation = resources.conversation_manager.create(
        tenant_id=tenant_id,
        owner_id=owner_id,
        title=request.title,
        workspace_id=request.workspace_id,
        participants=tuple(request.participants),
        security_classification=request.security_context.classification_clearance,
        session_id=session.session_id,
    )
    resources.session_manager.attach_conversation(
        tenant_id, session.session_id, conversation.conversation_id
    )
    logger.info(
        "conversation_started",
        extra={
            "conversation_id": conversation.conversation_id,
            "session_id": session.session_id,
        },
    )
    return StartConversationResponse(
        conversation_id=conversation.conversation_id,
        session_id=session.session_id,
        state=conversation.current_state,
    )


@router.post("/message", response_model=MessageResponse)
async def add_message(
    request: MessageRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> MessageResponse:
    """Add a user message and run the governed interaction loop."""
    _validate_security(resources, request.security_context, tenant_id)

    try:
        resources.session_manager.touch(tenant_id, request.session_id)
    except SessionError as exc:
        raise HTTPException(
            status_code=_SESSION_STATUS.get(
                exc.error_type, status.HTTP_400_BAD_REQUEST
            ),
            detail=exc.message,
        ) from exc

    try:
        result = resources.engine.handle_interaction(
            tenant_id, request.conversation_id, message=request.message
        )
    except ConversationError as exc:
        raise HTTPException(
            status_code=_CONVERSATION_STATUS.get(
                exc.error_type, status.HTTP_400_BAD_REQUEST
            ),
            detail=exc.message,
        ) from exc
    except IntentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=exc.message
        ) from exc

    classification = result.decision.classification
    return MessageResponse(
        interaction_id=result.interaction.interaction_id,
        conversation_state=result.conversation.current_state,
        intent=classification.intent,
        scope=classification.scope,
        confidence=classification.confidence,
        requires_clarification=classification.requires_clarification,
        clarification_prompt=classification.clarification_prompt,
        routing_target=result.decision.routing_target,
        assistant_response=result.interaction.assistant_response,
    )

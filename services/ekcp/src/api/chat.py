"""SSE streaming chat API contract and Server-Sent Events stub (EKCP-S0-5).

This module defines the streaming chat contract consumed by the Web UI sprint
track. The endpoint enforces the tenant header and security context ingress gate,
then streams a Server-Sent Events (SSE) response.

SSE event schema (each frame is ``event: <type>\\n`` followed by ``data: <json>``):

* ``token``    -- an incremental response fragment: ``{"text": "..."}``.
* ``citation`` -- a source citation for the response: a citation payload object
  ``{"document_id","chunk_id","source_path"}`` (emitted once real retrieval lands).
* ``done``     -- terminal success frame:
  ``{"session_id","correlation_id","finish_reason"}``.
* ``error``    -- terminal failure frame: ``{"error_type","message"}``.

Standard headers on every request: ``X-Tenant-ID`` (required) and
``X-Correlation-ID`` (generated when absent). ``X-Session-ID`` is optional.

S0 ships an echo stub: it streams the user's message back token by token and
emits a ``done`` frame. Real generation, citations, and token accounting arrive
with the model gateway (EKCP-S3) and knowledge integration (EKCP-S7).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies import AppSettings, TenantId
from domain.observability import get_correlation_id, get_logger, get_session_id
from domain.security import SecurityContextValidator, SecurityError

router = APIRouter(prefix="/chat", tags=["chat"])

logger = get_logger("ekcp.api.chat")

SSE_MEDIA_TYPE = "text/event-stream"


class SecurityContextPayload(BaseModel):
    """Security context carried on a chat request for the ingress gate."""

    user_id: str
    tenant_id: str
    classification_clearance: str


class ChatStreamRequest(BaseModel):
    """Request body for the streaming chat endpoint."""

    message: str = Field(min_length=1)
    security_context: SecurityContextPayload | None = None
    session_id: str | None = None


def format_sse_event(event: str, data: dict[str, object]) -> str:
    """Serialize a single Server-Sent Events frame."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


async def _echo_stream(message: str, *, session_id: str) -> AsyncIterator[str]:
    """Yield the S0 echo response as SSE frames (token frames then a done frame)."""
    for token in message.split():
        yield format_sse_event("token", {"text": token})
    yield format_sse_event(
        "done",
        {
            "session_id": session_id,
            "correlation_id": get_correlation_id(),
            "finish_reason": "stop",
        },
    )


@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
    tenant_id: TenantId,
    settings: AppSettings,
) -> StreamingResponse:
    """Stream a chat response as Server-Sent Events.

    Enforces the security context ingress gate before streaming. S0 returns an
    echo of the request message using the real SSE event schema so the Web UI can
    integrate against a stable contract ahead of model-backed generation.
    """
    validator = SecurityContextValidator.from_settings(settings.security)
    raw = request.security_context.model_dump() if request.security_context else None
    try:
        validator.validate(raw, expected_tenant_id=tenant_id)
    except SecurityError as exc:
        logger.warning("chat_stream_security_denied", extra={"error_type": exc.error_type})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    session_id = request.session_id or get_session_id() or str(uuid.uuid4())
    logger.info("chat_stream_started", extra={"session_id": session_id})
    return StreamingResponse(
        _echo_stream(request.message, session_id=session_id),
        media_type=SSE_MEDIA_TYPE,
    )

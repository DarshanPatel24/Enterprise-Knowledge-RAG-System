"""SSE streaming chat API backed by the model gateway (EKCP-S0 contract, S3 wiring).

Defines the streaming chat contract consumed by the Web UI. The endpoint enforces
the tenant header and security context ingress gate, then streams a Server-Sent
Events (SSE) response produced by the governed model gateway.

SSE event schema (each frame is ``event: <type>\\n`` followed by ``data: <json>``):

* ``token``    -- an incremental response fragment: ``{"text": "..."}``.
* ``citation`` -- a source citation for the response (emitted once knowledge
  integration lands in EKCP-S7).
* ``done``     -- terminal success frame:
  ``{"session_id","correlation_id","finish_reason","total_tokens","cost_estimate"}``.
* ``error``    -- terminal failure frame: ``{"error_type","message"}``.

Standard headers: ``X-Tenant-ID`` (required), ``X-Correlation-ID`` (generated when
absent), ``X-Session-ID`` (optional).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies import Resources, TenantId
from contracts.retrieval import RetrievalCandidate
from domain.gateway import GatewayError, GenerationRequest, StreamEventType
from domain.observability import get_correlation_id, get_logger, get_session_id
from domain.security import SecurityError

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

    message: str = Field(min_length=1, max_length=16000)
    security_context: SecurityContextPayload | None = None
    session_id: str | None = None


def format_sse_event(event: str, data: dict[str, object]) -> str:
    """Serialize a single Server-Sent Events frame."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def _build_grounded_prompt(message: str, candidates: list[RetrievalCandidate]) -> str:
    """Compose a grounded prompt from retrieved candidates and the user message."""
    context_block = "\n".join(
        f"- {candidate.content} [source: {candidate.citation.source_path}]"
        for candidate in candidates
    )
    return (
        "Use the following enterprise context to answer the question. "
        "Cite sources where relevant.\n\n"
        f"Context:\n{context_block}\n\nQuestion: {message}"
    )


async def _gateway_stream(
    resources: Resources,
    message: str,
    tenant_id: str,
    *,
    session_id: str,
    security_context: dict[str, str] | None,
) -> AsyncIterator[str]:
    """Stream a gateway response as SSE frames.

    When enterprise knowledge is available it emits ``citation`` frames for each
    retrieved source and grounds the prompt on that context; token frames and a
    terminal ``done`` frame follow. Knowledge failures degrade silently to an
    ungrounded response (the session never fails because EKRE is unavailable).
    """
    prompt_text = message
    if security_context is not None:
        result = resources.knowledge_retriever.retrieve(
            message,
            tenant_id=tenant_id,
            security_context=security_context,
            correlation_id=get_correlation_id(),
        )
        if result.has_knowledge and result.package is not None:
            candidates = result.package.candidates
            for candidate in candidates:
                citation = candidate.citation
                yield format_sse_event(
                    "citation",
                    {
                        "document_id": citation.document_id,
                        "chunk_id": citation.chunk_id,
                        "source_path": citation.source_path,
                        "confidence": candidate.relevance_score,
                        "explanation": candidate.explanation or "",
                    },
                )
            if candidates:
                prompt_text = _build_grounded_prompt(message, candidates)

    request = GenerationRequest(
        prompt_text=prompt_text,
        tenant_id=tenant_id,
        correlation_id=get_correlation_id(),
    )
    try:
        for event in resources.model_gateway.stream(request):
            if event.event_type is StreamEventType.TOKEN:
                yield format_sse_event("token", {"text": event.text})
            elif event.event_type is StreamEventType.ERROR:
                yield format_sse_event(
                    "error",
                    {"error_type": "provider_failed", "message": event.error_message},
                )
                return
            else:
                usage = event.token_usage
                yield format_sse_event(
                    "done",
                    {
                        "session_id": session_id,
                        "correlation_id": get_correlation_id(),
                        "finish_reason": event.finish_reason,
                        "total_tokens": usage.total_tokens if usage else 0,
                        "cost_estimate": event.cost_estimate,
                    },
                )
    except GatewayError as exc:
        yield format_sse_event(
            "error", {"error_type": exc.error_type, "message": exc.message}
        )


@router.post("/stream")
async def chat_stream(
    request: ChatStreamRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> StreamingResponse:
    """Stream a chat response as Server-Sent Events through the model gateway."""
    raw = request.security_context.model_dump() if request.security_context else None
    try:
        resources.security_validator.validate(raw, expected_tenant_id=tenant_id)
    except SecurityError as exc:
        logger.warning("chat_stream_security_denied", extra={"error_type": exc.error_type})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
        ) from exc

    session_id = request.session_id or get_session_id() or str(uuid.uuid4())
    logger.info("chat_stream_started", extra={"session_id": session_id})
    return StreamingResponse(
        _gateway_stream(
            resources,
            request.message,
            tenant_id,
            session_id=session_id,
            security_context=raw,
        ),
        media_type=SSE_MEDIA_TYPE,
    )

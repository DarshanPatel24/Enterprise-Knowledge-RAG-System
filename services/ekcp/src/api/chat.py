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

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from api.dependencies import Resources, TenantId
from contracts.retrieval import RetrievalCandidate
from domain.dialog import DialogMessage, TurnType, render_history
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


class ChatTurn(BaseModel):
    """A single prior message in the conversation carried for context."""

    role: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=16000)


class ChatStreamRequest(BaseModel):
    """Request body for the streaming chat endpoint."""

    message: str = Field(min_length=1, max_length=16000)
    security_context: SecurityContextPayload | None = None
    session_id: str | None = None
    # Prior turns of THIS conversation, oldest first, so the assistant can answer
    # follow-up questions in context. Retrieval still uses only ``message``; the
    # history conditions generation, not the knowledge search.
    history: list[ChatTurn] = Field(default_factory=list)


def format_sse_event(event: str, data: dict[str, object]) -> str:
    """Serialize a single Server-Sent Events frame."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


# Human-readable pipeline stage labels streamed to the UI so the user sees live
# progress instead of a single static spinner during the long retrieval and
# generation phases. Keys are stable; labels are display text.
_STAGE_LABELS: dict[str, str] = {
    "understanding": "Understanding your question",
    "clarifying": "Asking a quick clarifying question",
    "retrieving": "Retrieving relevant documents",
    "reranking": "Reranking for the best results",
    "reasoning": "Reasoning over the retrieved context",
    "generating": "Generating response",
}


def _stage_event(key: str) -> str:
    """Serialize a ``stage`` SSE frame carrying a pipeline progress label."""
    return format_sse_event("stage", {"key": key, "label": _STAGE_LABELS.get(key, key)})


def _citation_snippet(content: str, *, max_chars: int = 240) -> str:
    """Return a short, human-readable snippet of the cited chunk.

    Drops the leading breadcrumb context line (``> Context: ...``) and heading
    markers the chunker prepends, collapses whitespace, and truncates so the
    citation card shows readable source text rather than raw markdown.
    """
    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith((">", "#"))
    ]
    text = " ".join(lines) if lines else content.strip()
    text = " ".join(text.split())
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\u2026"
    return text


def _build_grounded_prompt(
    message: str, candidates: list[RetrievalCandidate], history_block: str = ""
) -> str:
    """Compose a strictly context-bounded prompt for the support assistant."""
    context_block = "\n\n".join(
        f"[{index}] {candidate.content}\n[source: {candidate.citation.source_path}]"
        for index, candidate in enumerate(candidates, start=1)
    )
    history_section = (
        f"=== CONVERSATION SO FAR ===\n{history_block}\n=== END CONVERSATION ===\n\n"
        if history_block
        else ""
    )
    return (
        "You are an expert enterprise knowledge assistant. Answer the QUESTION "
        "using ONLY the CONTEXT between the markers below.\n\n"
        "How to answer:\n"
        "- Read ALL of the CONTEXT passages before answering; the answer is often "
        "spread across several passages.\n"
        "- Be thorough and detailed. Synthesize the relevant passages into one "
        "coherent, complete answer rather than a terse summary. Do not omit "
        "relevant steps, conditions, values, or caveats that appear in the "
        "CONTEXT.\n"
        "- If the QUESTION has multiple parts, answer every part fully and label "
        "each part clearly.\n"
        "- Structure the answer for readability using Markdown: short headings, "
        "numbered steps for procedures, bullet points for lists, and tables when "
        "the CONTEXT presents mappings or comparisons.\n"
        "- If passages contain conflicting information, surface the conflict "
        "instead of silently choosing one.\n"
        "- The QUESTION may refer to the CONVERSATION SO FAR (for example a "
        "follow-up or pronoun); use it to interpret the QUESTION, but base every "
        "fact only on the CONTEXT.\n"
        "- Use only what the CONTEXT supports. Do not invent, assume, or add facts "
        "from outside knowledge. If the CONTEXT does not contain enough to answer "
        "(or a part of the answer), say so plainly for that part and suggest "
        "contacting support.\n"
        "- Cite the sources you rely on inline with their [source: ...] markers.\n\n"
        f"{history_section}"
        "=== CONTEXT START ===\n"
        f"{context_block}\n"
        "=== CONTEXT END ===\n\n"
        f"QUESTION: {message}"
    )


def _build_no_context_prompt(message: str, history_block: str = "") -> str:
    """Prompt used when no context was retrieved: force a grounded refusal."""
    history_section = (
        f"=== CONVERSATION SO FAR ===\n{history_block}\n=== END CONVERSATION ===\n\n"
        if history_block
        else ""
    )
    return (
        f"{history_section}"
        "No enterprise CONTEXT was retrieved for this question. Per your rules, "
        "tell the user the information is not available in the knowledge base and "
        "suggest contacting support. Do not answer from outside knowledge.\n\n"
        f"QUESTION: {message}"
    )


async def _client_gone(http_request: Request | None) -> bool:
    """Return whether the client has disconnected (pressed Stop or closed the tab).

    Used to stop the pipeline cooperatively so a cancelled request does not keep
    retrieving or generating in the background and holding scarce GPU resources.
    """
    return http_request is not None and await http_request.is_disconnected()


async def _gateway_stream(
    resources: Resources,
    message: str,
    tenant_id: str,
    *,
    session_id: str,
    security_context: dict[str, str] | None,
    history: list[ChatTurn] | None = None,
    http_request: Request | None = None,
) -> AsyncIterator[str]:
    """Stream a gateway response as SSE frames.

    Emits ``stage`` frames at each pipeline boundary so the UI shows live
    progress, then ``citation`` frames for each retrieved source, then ``token``
    frames and a terminal ``done`` frame. The blocking knowledge retrieval and
    model generation run in a worker thread (so the event loop is never frozen
    and every frame flushes to the client the moment it is produced). Knowledge
    failures degrade silently to an ungrounded response (the session never fails
    because EKRE is unavailable). Prior conversation turns (``history``) condition
    generation so follow-up questions are answered in context.
    """
    dialog_history = [
        DialogMessage(role=turn.role, content=turn.content)
        for turn in (history or [])
        if turn.content.strip()
    ]
    yield _stage_event("understanding")
    decision = resources.dialog_engine.decide(message, dialog_history)
    if decision.turn_type is TurnType.CLARIFICATION_NEEDED:
        yield _stage_event("clarifying")
        yield format_sse_event("token", {"text": decision.clarification_prompt})
        yield format_sse_event(
            "done",
            {
                "session_id": session_id,
                "correlation_id": get_correlation_id(),
                "finish_reason": "clarification",
                "total_tokens": 0,
                "cost_estimate": 0.0,
            },
        )
        return
    history_block = render_history(decision.history)
    prompt_text = _build_no_context_prompt(message, history_block)
    if security_context is not None:
        if await _client_gone(http_request):
            logger.info("chat_stream_cancelled", extra={"stage": "retrieving"})
            return
        yield _stage_event("retrieving")
        result = await run_in_threadpool(
            resources.knowledge_retriever.retrieve,
            decision.search_query,
            tenant_id=tenant_id,
            security_context=security_context,
            correlation_id=get_correlation_id(),
        )
        if await _client_gone(http_request):
            logger.info("chat_stream_cancelled", extra={"stage": "post_retrieval"})
            return
        if result.has_knowledge and result.package is not None:
            candidates = result.package.candidates
            if candidates:
                yield _stage_event("reranking")
            for candidate in candidates:
                citation = candidate.citation
                yield format_sse_event(
                    "citation",
                    {
                        "document_id": citation.document_id,
                        "chunk_id": citation.chunk_id,
                        "source_path": citation.source_path,
                        "section_title": citation.section_title or "",
                        "snippet": _citation_snippet(candidate.content),
                        "confidence": candidate.relevance_score,
                        "explanation": candidate.explanation or "",
                    },
                )
            if candidates:
                yield _stage_event("reasoning")
                prompt_text = _build_grounded_prompt(message, candidates, history_block)

    if await _client_gone(http_request):
        logger.info("chat_stream_cancelled", extra={"stage": "pre_generation"})
        return
    request = GenerationRequest(
        prompt_text=prompt_text,
        tenant_id=tenant_id,
        correlation_id=get_correlation_id(),
    )
    yield _stage_event("generating")
    try:
        async for event in iterate_in_threadpool(
            resources.model_gateway.stream(request)
        ):
            if await _client_gone(http_request):
                logger.info("chat_stream_cancelled", extra={"stage": "generating"})
                break
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
    http_request: Request,
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
            history=request.history,
            http_request=http_request,
        ),
        media_type=SSE_MEDIA_TYPE,
    )

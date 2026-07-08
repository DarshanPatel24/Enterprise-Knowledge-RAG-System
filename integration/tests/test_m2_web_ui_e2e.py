"""M2-S4: web UI end-to-end integration through EKCP.

Drives the exact contract the web UI consumes: a streaming chat request to EKCP
that retrieves enterprise knowledge (via a stub EKRE returning a citation),
grounds the response, and streams `token`, `citation`, and `done` SSE frames.
Validates gateway authentication, correlation-id propagation, and that citation
metadata (source path, confidence) reaches the client for card rendering.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from harness import clients
from harness.servers import EKCP_GATEWAY_TOKEN, ServiceHandle, launch_ekcp
from harness.stub_ekre import StubEkre

_TENANT = "tenant-a"
_SECURITY_CONTEXT = {
    "user_id": "u-1",
    "tenant_id": _TENANT,
    "classification_clearance": "internal",
}
_CANDIDATE = {
    "citation": {
        "document_id": "doc-9",
        "chunk_id": "chunk-1",
        "source_path": "/enterprise/retention.md",
    },
    "content": "Enterprise data retention is seven years.",
    "relevance_score": 0.91,
    "explanation": "policy match",
}


@pytest.fixture(scope="module")
def ekcp_with_citations() -> Iterator[str]:
    stub = StubEkre(candidates=[_CANDIDATE]).start()
    ekcp: ServiceHandle | None = None
    try:
        ekcp = launch_ekcp(port=18023, knowledge_base_url=stub.base_url)
        yield ekcp.base_url
    finally:
        if ekcp is not None:
            ekcp.stop()
        stub.stop()


def test_chat_stream_end_to_end_with_citations(ekcp_with_citations: str) -> None:
    correlation_id = "e2e-correlation-1"
    status, headers, events = clients.stream_sse(
        ekcp_with_citations,
        "/chat/stream",
        tenant_id=_TENANT,
        auth_token=EKCP_GATEWAY_TOKEN,
        correlation_id=correlation_id,
        payload={
            "message": "What is the data retention policy?",
            "security_context": _SECURITY_CONTEXT,
        },
    )

    assert status == 200
    assert headers.get("content-type", "").startswith("text/event-stream")
    assert headers.get("x-correlation-id") == correlation_id

    tokens = [data for name, data in events if name == "token"]
    citations = [data for name, data in events if name == "citation"]
    done = [data for name, data in events if name == "done"]

    assert tokens, "expected streamed token frames"
    assert done and len(done) == 1, "expected exactly one terminal done frame"
    assert done[0]["correlation_id"] == correlation_id

    assert citations, "expected at least one citation frame"
    cited: dict[str, Any] = citations[0]
    assert cited["source_path"] == "/enterprise/retention.md"
    assert cited["document_id"] == "doc-9"
    assert float(cited["confidence"]) == pytest.approx(0.91)


def test_chat_stream_requires_gateway_token(ekcp_with_citations: str) -> None:
    status, _headers, _events = clients.stream_sse(
        ekcp_with_citations,
        "/chat/stream",
        tenant_id=_TENANT,
        payload={"message": "hello", "security_context": _SECURITY_CONTEXT},
    )
    assert status == 401

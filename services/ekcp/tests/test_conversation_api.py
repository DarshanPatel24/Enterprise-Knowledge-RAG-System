"""Conversation API tests: start and message endpoints."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import build_resources, get_resources
from config.settings import EkcpSettings

_CONTEXT = {
    "user_id": "analyst-1",
    "tenant_id": "tenant-a",
    "classification_clearance": "internal",
}


def _client(settings: EkcpSettings) -> AsyncClient:
    app = create_app(settings)
    resources = build_resources(settings)
    app.dependency_overrides[get_resources] = lambda: resources
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://ekcp.test")


@pytest.fixture
def settings() -> EkcpSettings:
    return EkcpSettings(_env_file=None)


async def _start(client: AsyncClient) -> tuple[str, str]:
    response = await client.post(
        "/conversation/start",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"security_context": _CONTEXT, "title": "Support"},
    )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    return body["conversation_id"], body["session_id"]


async def test_start_conversation(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/conversation/start",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT},
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["conversation_id"].startswith("conv-")
    assert body["session_id"].startswith("sess-")
    assert body["state"] == "created"


async def test_message_organizational_routes_to_knowledge(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        conversation_id, session_id = await _start(client)
        response = await client.post(
            "/conversation/message",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": conversation_id,
                "session_id": session_id,
                "message": "What is the company policy on remote work?",
                "security_context": _CONTEXT,
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["conversation_state"] == "active"
    assert body["scope"] == "organizational"
    assert body["routing_target"] == "knowledge"
    assert body["requires_clarification"] is False


async def test_message_ambiguous_requests_clarification(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        conversation_id, session_id = await _start(client)
        response = await client.post(
            "/conversation/message",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": conversation_id,
                "session_id": session_id,
                "message": "hmm",
                "security_context": _CONTEXT,
            },
        )
    body = response.json()
    assert body["requires_clarification"] is True
    assert body["conversation_state"] == "waiting"
    assert body["clarification_prompt"]


async def test_message_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        conversation_id, session_id = await _start(client)
        response = await client.post(
            "/conversation/message",
            json={
                "conversation_id": conversation_id,
                "session_id": session_id,
                "message": "hello",
                "security_context": _CONTEXT,
            },
        )
    assert response.status_code == httpx.codes.BAD_REQUEST


async def test_message_denies_tenant_mismatch(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        conversation_id, session_id = await _start(client)
        response = await client.post(
            "/conversation/message",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": conversation_id,
                "session_id": session_id,
                "message": "hello",
                "security_context": {**_CONTEXT, "tenant_id": "tenant-b"},
            },
        )
    assert response.status_code == httpx.codes.FORBIDDEN


async def test_message_unknown_conversation_404(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        _, session_id = await _start(client)
        response = await client.post(
            "/conversation/message",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": "conv-missing",
                "session_id": session_id,
                "message": "What is the company policy?",
                "security_context": _CONTEXT,
            },
        )
    assert response.status_code == httpx.codes.NOT_FOUND

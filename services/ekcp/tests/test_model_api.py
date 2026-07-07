"""Model gateway and streaming chat API tests."""

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


async def test_invoke_model_with_prompt_text(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/model/invoke",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "prompt_text": "User request: what is the remote work policy?",
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["model_id"] == "ekcp-echo"
    assert body["output"]
    assert body["token_usage"]["total_tokens"] > 0


async def test_invoke_model_via_context_id(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        build = await client.post(
            "/context/build",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": "conv-1",
                "user_intent": "What is the remote work policy?",
                "security_context": _CONTEXT,
            },
        )
        context_id = build.json()["context_id"]
        response = await client.post(
            "/model/invoke",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT, "context_id": context_id},
        )
    assert response.status_code == httpx.codes.OK
    assert response.json()["output"]


async def test_invoke_requires_prompt_or_context(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/model/invoke",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT},
        )
    assert response.status_code == httpx.codes.UNPROCESSABLE_ENTITY


async def test_invoke_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/model/invoke",
            json={"security_context": _CONTEXT, "prompt_text": "hello world"},
        )
    assert response.status_code == httpx.codes.BAD_REQUEST


async def test_chat_stream_produces_gateway_tokens(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/chat/stream",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "message": "What is the remote work policy?",
                "security_context": _CONTEXT,
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.text
    assert "event: token" in body
    assert "event: done" in body
    assert "total_tokens" in body


async def test_chat_stream_denies_tenant_mismatch(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/chat/stream",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "message": "hello",
                "security_context": {**_CONTEXT, "tenant_id": "tenant-b"},
            },
        )
    assert response.status_code == httpx.codes.FORBIDDEN

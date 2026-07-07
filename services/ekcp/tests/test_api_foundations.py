"""API foundation tests: health probes and the SSE streaming chat contract."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import get_app_settings
from config.settings import EkcpSettings

_VALID_CONTEXT = {
    "user_id": "analyst-1",
    "tenant_id": "tenant-a",
    "classification_clearance": "internal",
}


def _client(settings: EkcpSettings) -> AsyncClient:
    app = create_app(settings)
    app.dependency_overrides[get_app_settings] = lambda: settings
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://ekcp.test")


@pytest.fixture
def settings() -> EkcpSettings:
    return EkcpSettings(_env_file=None)


async def test_health_live_and_ready(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        live = await client.get("/health/live")
        ready = await client.get("/health/ready")
    assert live.status_code == httpx.codes.OK
    assert live.json() == {"status": "ok", "service": "ekcp"}
    assert ready.json()["status"] == "ready"


async def test_chat_stream_echoes_sse_events(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/chat/stream",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"message": "hello world", "security_context": _VALID_CONTEXT},
        )
    assert response.status_code == httpx.codes.OK
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: token" in body
    assert '"text": "hello"' in body
    assert '"text": "world"' in body
    assert "event: done" in body
    assert response.headers["X-Correlation-ID"]


async def test_chat_stream_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/chat/stream",
            json={"message": "hello", "security_context": _VALID_CONTEXT},
        )
    assert response.status_code == httpx.codes.BAD_REQUEST


async def test_chat_stream_denies_missing_security_context(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/chat/stream",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"message": "hello"},
        )
    assert response.status_code == httpx.codes.FORBIDDEN


async def test_chat_stream_denies_tenant_mismatch(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/chat/stream",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "message": "hello",
                "security_context": {**_VALID_CONTEXT, "tenant_id": "tenant-b"},
            },
        )
    assert response.status_code == httpx.codes.FORBIDDEN

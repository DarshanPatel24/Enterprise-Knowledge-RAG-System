"""Memory API tests: store, retrieve, consolidate, purge, and context integration."""

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


async def _store(client: AsyncClient, content: str, **extra: object) -> dict:
    response = await client.post(
        "/memory/store",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"security_context": _CONTEXT, "content": content, **extra},
    )
    assert response.status_code == httpx.codes.OK
    return response.json()


async def test_store_then_retrieve(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        stored = await _store(
            client, "User prefers JSON responses", memory_type="preference", scope="user"
        )
        assert stored["memory_id"].startswith("mem-")
        assert stored["confidence"] == 0.95

        response = await client.post(
            "/memory/retrieve",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT, "query": "JSON responses"},
        )
    assert response.status_code == httpx.codes.OK
    hits = response.json()["hits"]
    assert hits
    assert "JSON" in hits[0]["content"]


async def test_consolidate_and_purge(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        await _store(
            client,
            "Decided to launch in Q3",
            memory_type="decision",
            scope="conversation",
            conversation_id="conv-1",
        )
        consolidate = await client.post(
            "/memory/consolidate",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT, "conversation_id": "conv-1"},
        )
        assert consolidate.status_code == httpx.codes.OK
        assert consolidate.json()["source_count"] == 1

        purge = await client.post(
            "/memory/purge",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT, "conversation_id": "conv-1"},
        )
    assert purge.status_code == httpx.codes.OK
    assert purge.json()["deleted_count"] >= 1


async def test_consolidate_without_memories_404(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/memory/consolidate",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT, "conversation_id": "missing"},
        )
    assert response.status_code == httpx.codes.NOT_FOUND


async def test_memory_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/memory/store",
            json={"security_context": _CONTEXT, "content": "note"},
        )
    assert response.status_code == httpx.codes.BAD_REQUEST


async def test_context_build_includes_memory(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        await _store(
            client, "User prefers dark mode", memory_type="preference", scope="user"
        )
        response = await client.post(
            "/context/build",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": "conv-1",
                "user_intent": "what are the user prefers settings",
                "security_context": _CONTEXT,
                "include_memory": True,
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["selected_count"] >= 1

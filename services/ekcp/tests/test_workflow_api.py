"""Workflow API tests plus knowledge degradation on context build."""

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


async def _trigger(client: AsyncClient) -> str:
    response = await client.post(
        "/workflow/trigger",
        headers={"X-Tenant-ID": "tenant-a"},
        json={
            "security_context": _CONTEXT,
            "objective": "retrieve sales data, generate report, notify stakeholders",
        },
    )
    assert response.status_code == httpx.codes.OK
    return response.json()["workflow_id"]


async def test_trigger_and_get_workflow(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        workflow_id = await _trigger(client)
        get = await client.get(
            f"/workflow/{workflow_id}", headers={"X-Tenant-ID": "tenant-a"}
        )
    assert get.status_code == httpx.codes.OK
    body = get.json()
    assert body["state"] == "planned"
    assert body["plan_id"] is not None
    assert body["task_count"] >= 2


async def test_pause_resume_approve(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        workflow_id = await _trigger(client)
        pause = await client.post(
            f"/workflow/{workflow_id}/pause",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT},
        )
        assert pause.json()["state"] == "paused"
        approve = await client.post(
            f"/workflow/{workflow_id}/approve",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT},
        )
    assert approve.json()["state"] == "executing"


async def test_get_missing_workflow_404(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.get(
            "/workflow/wf-missing", headers={"X-Tenant-ID": "tenant-a"}
        )
    assert response.status_code == httpx.codes.NOT_FOUND


async def test_trigger_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/workflow/trigger",
            json={"security_context": _CONTEXT, "objective": "do it"},
        )
    assert response.status_code == httpx.codes.BAD_REQUEST


async def test_context_build_degrades_when_knowledge_disabled(
    settings: EkcpSettings,
) -> None:
    # Knowledge is disabled by default, so include_knowledge degrades to local
    # context without failing the request.
    async with _client(settings) as client:
        response = await client.post(
            "/context/build",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": "conv-1",
                "user_intent": "What is the remote work policy?",
                "security_context": _CONTEXT,
                "conversation_history": ["hello"],
                "include_knowledge": True,
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["degraded"] is True
    assert any("degraded" in warning for warning in body["warnings"])

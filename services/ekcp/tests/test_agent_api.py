"""Agent API tests: execute and plan endpoints."""

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


async def test_execute_reasoning_agent(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/execute",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "task_description": "Summarize the remote work policy",
                "capability": "reasoning",
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["agent_id"] == "planner-agent"
    assert body["status"] == "completed"
    assert body["result"]


async def test_execute_research_agent_with_permission(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/execute",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "task_description": "Find the leave policy",
                "capability": "research",
                "granted_permissions": ["tool:knowledge_search"],
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["agent_id"] == "research-agent"
    assert body["tool_usage"]
    assert body["tool_usage"][0]["tool_id"] == "knowledge_search"


async def test_execute_research_without_permission_404(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/execute",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "task_description": "Find the leave policy",
                "capability": "research",
            },
        )
    assert response.status_code == httpx.codes.NOT_FOUND


async def test_execute_unknown_capability_422(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/execute",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "task_description": "do something",
                "capability": "telepathy",
            },
        )
    assert response.status_code == httpx.codes.UNPROCESSABLE_ENTITY


async def test_execute_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/execute",
            json={
                "security_context": _CONTEXT,
                "task_description": "x",
                "capability": "reasoning",
            },
        )
    assert response.status_code == httpx.codes.BAD_REQUEST


async def test_plan_endpoint(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/plan",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "objective": (
                    "retrieve sales data, generate report, obtain approval, notify"
                ),
            },
        )
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["plan_id"].startswith("plan-")
    assert body["execution_strategy"] == "conditional"
    assert len(body["tasks"]) >= 3
    assert body["approval_checkpoints"]

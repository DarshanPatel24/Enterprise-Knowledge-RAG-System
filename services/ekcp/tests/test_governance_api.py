"""Governance API tests plus governed enforcement on agent/memory endpoints."""

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


async def test_evaluate_grant_and_deny(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        grant = await client.post(
            "/governance/evaluate",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "permission": "invoke_agent",
                "resource": "research-agent",
                "roles": ["power_user"],
            },
        )
        deny = await client.post(
            "/governance/evaluate",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "permission": "invoke_agent",
                "resource": "research-agent",
                "roles": ["user"],
            },
        )
    assert grant.json()["allowed"] is True
    assert deny.json()["allowed"] is False
    assert "role_missing_permission" in deny.json()["reason"]


async def test_agent_execute_denied_for_restricted_role(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/execute",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "task_description": "do something",
                "capability": "reasoning",
                "roles": ["user"],
            },
        )
    assert response.status_code == httpx.codes.FORBIDDEN


async def test_agent_execute_allowed_default_role(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/agent/execute",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "task_description": "Summarize the policy",
                "capability": "reasoning",
            },
        )
    assert response.status_code == httpx.codes.OK


async def test_audit_trail_records_governed_operations(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        await client.post(
            "/agent/execute",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "task_description": "Summarize the policy",
                "capability": "reasoning",
            },
        )
        audit = await client.get(
            "/governance/audit", headers={"X-Tenant-ID": "tenant-a"}
        )
    body = audit.json()
    assert body["total"] >= 1
    actions = [record["action"] for record in body["records"]]
    assert "agent_invoked" in actions


async def test_model_invoke_masks_pii(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/model/invoke",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "prompt_text": "User request: reply exactly with jane@acme.com",
            },
        )
    # The deterministic echo repeats the request text, which contains an email;
    # governance masks it before the response leaves the platform.
    assert response.status_code == httpx.codes.OK
    assert "jane@acme.com" not in response.json()["output"]


async def test_evaluate_requires_tenant(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/governance/evaluate",
            json={
                "security_context": _CONTEXT,
                "permission": "invoke_agent",
                "resource": "x",
            },
        )
    assert response.status_code == httpx.codes.BAD_REQUEST

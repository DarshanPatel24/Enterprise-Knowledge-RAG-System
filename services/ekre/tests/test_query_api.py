"""Tests for the query planning API endpoint."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import get_app_settings
from config.settings import EkreSettings


def _client(settings: EkreSettings) -> AsyncClient:
    app = create_app(settings)
    app.dependency_overrides[get_app_settings] = lambda: settings
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture
def hermetic_settings() -> EkreSettings:
    return EkreSettings(_env_file=None)


def _body(query: str = "compare EKIE and EKRE", tenant: str = "tenant-a") -> dict[str, object]:
    return {
        "query": query,
        "security_context": {
            "user_id": "analyst-1",
            "tenant_id": tenant,
            "classification_clearance": "internal",
        },
    }


async def test_plan_query_returns_structured_query(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.post(
            "/v1/query/plan", json=_body(), headers={"X-Tenant-ID": "tenant-a"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["intent"] == "comparison"
    assert body["plan"]["steps"]
    assert body["tenant_id"] == "tenant-a"


async def test_plan_query_requires_tenant_header(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.post("/v1/query/plan", json=_body())
    assert response.status_code == 400


async def test_plan_query_rejects_tenant_mismatch(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.post(
            "/v1/query/plan",
            json=_body(tenant="tenant-b"),
            headers={"X-Tenant-ID": "tenant-a"},
        )
    assert response.status_code == 403

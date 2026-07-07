"""Tests for the full observable retrieval API endpoint."""

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


async def test_retrieve_returns_traced_result(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.post(
            "/v1/query/retrieve", json=_body(), headers={"X-Tenant-ID": "tenant-a"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["package"]["tenant_id"] == "tenant-a"
    assert body["package"]["security_filtered"] is True
    # The execution trace exposes the full stage timeline.
    stages = {s["stage"] for s in body["trace"]["stages"]}
    assert {"query_understanding", "execution", "assembly", "masking"} <= stages
    assert body["trace"]["execution_id"].startswith("exec-")


async def test_retrieve_requires_tenant(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.post("/v1/query/retrieve", json=_body())
    assert response.status_code == 400


async def test_retrieve_rejects_tenant_mismatch(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.post(
            "/v1/query/retrieve",
            json=_body(tenant="tenant-b"),
            headers={"X-Tenant-ID": "tenant-a"},
        )
    assert response.status_code == 403

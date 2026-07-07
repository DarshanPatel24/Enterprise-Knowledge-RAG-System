"""Tests for the EKRE API foundations (health + retrieval config)."""

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


async def test_health_live(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["service"] == "ekre"


async def test_health_ready(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_retrieval_config_requires_tenant(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.get("/v1/retrieval/config")
    assert response.status_code == 400


async def test_retrieval_config_returns_profile(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.get(
            "/v1/retrieval/config", headers={"X-Tenant-ID": "tenant-a"}
        )
    assert response.status_code == 200
    body = response.json()
    # No live Qdrant in the test environment -> configured fallback is reported,
    # proving the model/metric are never hardcoded in the response path.
    assert body["source"] == "fallback"
    assert body["collection"] == "enterprise_documents"
    assert set(body["latency_budgets_ms"]) == {
        "query_understanding",
        "vector",
        "ranking",
        "assembly",
        "total",
    }
    assert "X-Correlation-ID" in response.headers

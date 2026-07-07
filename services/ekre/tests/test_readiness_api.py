"""Tests for the deployment readiness API endpoint."""

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


async def test_readiness_returns_report(hermetic_settings: EkreSettings) -> None:
    async with _client(hermetic_settings) as client:
        response = await client.get("/v1/readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "deployment"
    checks = {f["check"] for f in body["findings"]}
    assert "worker_pool" in checks
    assert "high_availability" in checks

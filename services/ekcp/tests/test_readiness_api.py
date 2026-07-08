"""Deployment, multi-tenancy, and master handoff readiness API tests."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from config.settings import EkcpSettings


def _client(settings: EkcpSettings) -> AsyncClient:
    app = create_app(settings)
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://ekcp.test")


@pytest.fixture
def settings() -> EkcpSettings:
    return EkcpSettings(_env_file=None)


async def test_deployment_readiness_endpoint(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.get("/v1/readiness")
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["name"] == "deployment"
    assert body["ready"] is True


async def test_tenancy_readiness_endpoint(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.get("/v1/readiness/tenancy")
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["name"] == "multi_tenancy"
    assert body["ready"] is True


async def test_handoff_readiness_endpoint(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.get("/v1/readiness/handoff")
    assert response.status_code == httpx.codes.OK
    body = response.json()
    assert body["service"] == "ekcp"
    assert body["ready"] is True
    assert "POST /chat/stream" in body["endpoints"]
    assert body["report"]["name"] == "master_handoff"

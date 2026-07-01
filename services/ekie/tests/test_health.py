"""Tests for the FastAPI application and health endpoints."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.middleware import CORRELATION_HEADER


@pytest.fixture
def app() -> FastAPI:
    return create_app()


async def test_liveness_returns_ok(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ekie"}


async def test_readiness_returns_ready(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_correlation_header_is_returned(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live")
    assert CORRELATION_HEADER in response.headers
    assert response.headers[CORRELATION_HEADER]


async def test_correlation_header_is_echoed_when_provided(app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/live", headers={CORRELATION_HEADER: "corr-xyz"})
    assert response.headers[CORRELATION_HEADER] == "corr-xyz"

"""Ingress security guard tests: gateway authentication and tenant admission."""

from __future__ import annotations

import httpx
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import build_resources, get_resources
from config.settings import EkcpSettings

_CONTEXT = {
    "user_id": "u1",
    "tenant_id": "tenant-a",
    "classification_clearance": "internal",
}
_START_BODY = {"security_context": _CONTEXT, "title": "T"}


def _client(settings: EkcpSettings) -> tuple[AsyncClient, object]:
    app = create_app(settings)
    resources = build_resources(settings)
    app.dependency_overrides[get_resources] = lambda: resources
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://ekcp.test"), app


def _auth_settings() -> EkcpSettings:
    return EkcpSettings(
        _env_file=None,
        security={  # type: ignore[arg-type]
            "require_gateway_auth": True,
            "gateway_auth_token": "s3cret-token",
        },
    )


async def test_missing_gateway_token_is_rejected() -> None:
    client, _ = _client(_auth_settings())
    async with client:
        response = await client.post(
            "/conversation/start", headers={"X-Tenant-ID": "tenant-a"}, json=_START_BODY
        )
    assert response.status_code == httpx.codes.UNAUTHORIZED


async def test_invalid_gateway_token_is_rejected() -> None:
    client, _ = _client(_auth_settings())
    async with client:
        response = await client.post(
            "/conversation/start",
            headers={"X-Tenant-ID": "tenant-a", "Authorization": "Bearer wrong"},
            json=_START_BODY,
        )
    assert response.status_code == httpx.codes.UNAUTHORIZED


async def test_valid_gateway_token_is_accepted() -> None:
    client, _ = _client(_auth_settings())
    async with client:
        response = await client.post(
            "/conversation/start",
            headers={
                "X-Tenant-ID": "tenant-a",
                "Authorization": "Bearer s3cret-token",
            },
            json=_START_BODY,
        )
    assert response.status_code == httpx.codes.OK


async def test_x_service_token_header_is_accepted() -> None:
    client, _ = _client(_auth_settings())
    async with client:
        response = await client.post(
            "/conversation/start",
            headers={"X-Tenant-ID": "tenant-a", "X-Service-Token": "s3cret-token"},
            json=_START_BODY,
        )
    assert response.status_code == httpx.codes.OK


async def test_gateway_auth_required_but_unconfigured_fails_closed() -> None:
    settings = EkcpSettings(
        _env_file=None,
        security={"require_gateway_auth": True, "gateway_auth_token": ""},  # type: ignore[arg-type]
    )
    client, _ = _client(settings)
    async with client:
        response = await client.post(
            "/conversation/start", headers={"X-Tenant-ID": "tenant-a"}, json=_START_BODY
        )
    assert response.status_code == httpx.codes.SERVICE_UNAVAILABLE


async def test_health_is_open_without_gateway_token() -> None:
    client, _ = _client(_auth_settings())
    async with client:
        response = await client.get("/health/live")
    assert response.status_code == httpx.codes.OK


async def test_tenant_concurrency_limit_rejects_when_full() -> None:
    settings = EkcpSettings(
        _env_file=None,
        deployment={"tenant_max_concurrent": 1},  # type: ignore[arg-type]
    )
    client, app = _client(settings)
    # Fill the single admission slot for tenant-a before the request runs.
    app.state.tenant_limiter.acquire("tenant-a")  # type: ignore[attr-defined]
    async with client:
        response = await client.post(
            "/conversation/start", headers={"X-Tenant-ID": "tenant-a"}, json=_START_BODY
        )
    assert response.status_code == httpx.codes.TOO_MANY_REQUESTS


async def test_tenant_concurrency_slot_released_after_request() -> None:
    settings = EkcpSettings(
        _env_file=None,
        deployment={"tenant_max_concurrent": 1},  # type: ignore[arg-type]
    )
    client, app = _client(settings)
    async with client:
        first = await client.post(
            "/conversation/start", headers={"X-Tenant-ID": "tenant-a"}, json=_START_BODY
        )
        second = await client.post(
            "/conversation/start", headers={"X-Tenant-ID": "tenant-a"}, json=_START_BODY
        )
    assert first.status_code == httpx.codes.OK
    assert second.status_code == httpx.codes.OK
    assert app.state.tenant_limiter.active("tenant-a") == 0  # type: ignore[attr-defined]


async def test_oversized_message_is_rejected() -> None:
    client, _ = _client(EkcpSettings(_env_file=None))
    async with client:
        start = await client.post(
            "/conversation/start", headers={"X-Tenant-ID": "tenant-a"}, json=_START_BODY
        )
        ids = start.json()
        response = await client.post(
            "/conversation/message",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "conversation_id": ids["conversation_id"],
                "session_id": ids["session_id"],
                "message": "x" * 16001,
                "security_context": _CONTEXT,
            },
        )
    assert response.status_code == httpx.codes.UNPROCESSABLE_ENTITY

"""Ingress security guards: gateway authentication and tenant admission control.

These guards run before governed routes. ``verify_gateway_auth`` enforces that
only the trusted upstream gateway can reach EKCP (shared bearer token), closing
the trust boundary the RBAC/ABAC layer depends on. ``enforce_tenant_limit``
applies per-tenant concurrency admission control to bound resource exhaustion.

Both read their configuration and the per-application limiter from ``app.state``
so they honor the exact settings the running app was built with (never global
state), keeping tests hermetic.
"""

from __future__ import annotations

import hmac
from collections.abc import Iterator

from fastapi import HTTPException, status
from starlette.requests import Request

from config.settings import SecuritySettings
from domain.observability import get_logger
from domain.readiness import TenantConcurrencyLimiter

logger = get_logger("ekcp.api.guards")

_BEARER_PREFIX = "Bearer "


def _extract_token(request: Request) -> str:
    """Extract a bearer token from the Authorization or X-Service-Token header."""
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith(_BEARER_PREFIX):
        return authorization[len(_BEARER_PREFIX) :].strip()
    return request.headers.get("X-Service-Token", "").strip()


def verify_gateway_auth(request: Request) -> None:
    """Reject requests that do not present the trusted gateway token when required."""
    security: SecuritySettings | None = getattr(
        request.app.state, "security_settings", None
    )
    if security is None or not security.require_gateway_auth:
        return
    expected = security.gateway_auth_token
    if not expected:
        # Fail closed: auth is required but no token is configured.
        logger.error("gateway_auth_misconfigured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="gateway authentication is required but not configured",
        )
    presented = _extract_token(request)
    if not presented or not hmac.compare_digest(presented, expected):
        logger.warning("gateway_auth_denied")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid gateway authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def enforce_tenant_limit(request: Request) -> Iterator[None]:
    """Admit at most ``tenant_max_concurrent`` in-flight requests per tenant."""
    limiter: TenantConcurrencyLimiter | None = getattr(
        request.app.state, "tenant_limiter", None
    )
    tenant_id = request.headers.get("X-Tenant-ID", "").strip()
    if limiter is None or not tenant_id:
        yield
        return
    if not limiter.acquire(tenant_id):
        logger.warning("tenant_admission_rejected", extra={"tenant_id": tenant_id})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="tenant concurrency limit exceeded; retry shortly",
            headers={"Retry-After": "1"},
        )
    try:
        yield
    finally:
        limiter.release(tenant_id)

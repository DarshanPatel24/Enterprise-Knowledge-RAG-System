"""Correlation middleware binding tenant, correlation, and query ids per request."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from domain.observability.context import (
    set_correlation_id,
    set_query_id,
    set_tenant_id,
)
from domain.resilience import TenantConcurrencyLimiter

CORRELATION_HEADER = "X-Correlation-ID"
TENANT_HEADER = "X-Tenant-ID"
QUERY_HEADER = "X-Query-ID"
_QUOTA_SCOPED_PREFIX = "/v1/query"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Bind ``correlation_id``, ``tenant_id``, and ``query_id`` from headers.

    A correlation id and query id are generated when the inbound request does not
    supply them, guaranteeing every request and its logs are traceable end to end.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
        query_id = request.headers.get(QUERY_HEADER) or str(uuid.uuid4())
        tenant_id = request.headers.get(TENANT_HEADER)

        correlation_token = set_correlation_id(correlation_id)
        query_token = set_query_id(query_id)
        tenant_token = set_tenant_id(tenant_id)
        try:
            response = await call_next(request)
        finally:
            tenant_token.var.reset(tenant_token)
            query_token.var.reset(query_token)
            correlation_token.var.reset(correlation_token)

        response.headers[CORRELATION_HEADER] = correlation_id
        response.headers[QUERY_HEADER] = query_id
        return response


class TenantQuotaMiddleware(BaseHTTPMiddleware):
    """Enforce a per-tenant concurrency ceiling on retrieval requests.

    Applies only to the retrieval endpoints (``/v1/query``); health, readiness,
    and configuration endpoints are never throttled. A tenant that exceeds its
    ceiling receives ``429 Too Many Requests`` so no single tenant can exhaust
    shared retrieval capacity. The limiter is read from application state.
    """

    def __init__(self, app: object, limiter: TenantConcurrencyLimiter) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._limiter = limiter

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        tenant_id = request.headers.get(TENANT_HEADER)
        if not request.url.path.startswith(_QUOTA_SCOPED_PREFIX) or not tenant_id:
            return await call_next(request)
        if not self._limiter.acquire(tenant_id):
            return JSONResponse(
                status_code=429,
                content={"detail": "tenant concurrency limit exceeded"},
            )
        try:
            return await call_next(request)
        finally:
            self._limiter.release(tenant_id)

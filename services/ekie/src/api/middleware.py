"""Correlation middleware binding tenant and correlation ids per request."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from domain.observability.context import set_correlation_id, set_tenant_id

CORRELATION_HEADER = "X-Correlation-ID"
TENANT_HEADER = "X-Tenant-ID"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Bind ``correlation_id`` and ``tenant_id`` from request headers.

    A correlation id is generated when the inbound request does not supply one,
    guaranteeing every request and its logs are traceable end to end.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
        tenant_id = request.headers.get(TENANT_HEADER)

        correlation_token = set_correlation_id(correlation_id)
        tenant_token = set_tenant_id(tenant_id)
        try:
            response = await call_next(request)
        finally:
            correlation_token.var.reset(correlation_token)
            tenant_token.var.reset(tenant_token)

        response.headers[CORRELATION_HEADER] = correlation_id
        return response

"""HTTP client helpers for driving engine REST APIs with standard headers.

Every cross-engine request carries ``X-Tenant-ID`` and ``X-Correlation-ID``,
mirroring the headers the production services require and log.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx


def new_correlation_id() -> str:
    """Return a fresh correlation identifier."""
    return str(uuid.uuid4())


def engine_headers(
    tenant_id: str,
    *,
    correlation_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, str]:
    """Build the standard cross-engine header set."""
    headers = {
        "X-Tenant-ID": tenant_id,
        "X-Correlation-ID": correlation_id or new_correlation_id(),
        "Content-Type": "application/json",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    return headers


def post_json(
    base_url: str,
    path: str,
    *,
    tenant_id: str,
    json: dict[str, Any],
    correlation_id: str | None = None,
    auth_token: str | None = None,
    timeout: float = 30.0,
) -> httpx.Response:
    """POST a JSON body to an engine endpoint with the standard headers."""
    return httpx.post(
        f"{base_url}{path}",
        headers=engine_headers(
            tenant_id, correlation_id=correlation_id, auth_token=auth_token
        ),
        json=json,
        timeout=timeout,
    )


def get(
    base_url: str,
    path: str,
    *,
    tenant_id: str | None = None,
    timeout: float = 10.0,
) -> httpx.Response:
    """GET an engine endpoint, optionally with the tenant header."""
    headers = {"X-Tenant-ID": tenant_id} if tenant_id else {}
    return httpx.get(f"{base_url}{path}", headers=headers, timeout=timeout)


def stream_sse(
    base_url: str,
    path: str,
    *,
    tenant_id: str,
    payload: dict[str, Any],
    auth_token: str | None = None,
    correlation_id: str | None = None,
    timeout: float = 30.0,
) -> tuple[int, httpx.Headers, list[tuple[str, dict[str, Any]]]]:
    """POST and consume a Server-Sent Events stream into parsed (event, data) frames."""
    headers = engine_headers(
        tenant_id, correlation_id=correlation_id, auth_token=auth_token
    )
    events: list[tuple[str, dict[str, Any]]] = []
    with httpx.stream(
        "POST", f"{base_url}{path}", headers=headers, json=payload, timeout=timeout
    ) as response:
        status_code = response.status_code
        response_headers = response.headers
        if status_code == 200:
            event_name = ""
            for line in response.iter_lines():
                if line.startswith("event:"):
                    event_name = line[len("event:") :].strip()
                elif line.startswith("data:"):
                    data = json.loads(line[len("data:") :].strip())
                    events.append((event_name, data))
                    event_name = ""
    return status_code, response_headers, events

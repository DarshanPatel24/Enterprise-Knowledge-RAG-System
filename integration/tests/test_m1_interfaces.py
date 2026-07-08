"""M1-S2: live cross-engine interface validation.

Boots EKRE and EKCP as real localhost processes and exercises the production
boundary EKCP -> EKRE (`/context/build` with knowledge -> `/v1/query/retrieve`),
plus health/readiness probes and the security ingress gate.
"""

from __future__ import annotations

from typing import Any

from harness import clients
from harness.servers import EKCP_GATEWAY_TOKEN

_TENANT = "tenant-a"
_SECURITY_CONTEXT = {
    "user_id": "u-1",
    "tenant_id": _TENANT,
    "classification_clearance": "internal",
}


def test_health_and_readiness_endpoints(ekre_and_ekcp: dict[str, str]) -> None:
    for base_url in ekre_and_ekcp.values():
        assert clients.get(base_url, "/health/live").status_code == 200
    assert clients.get(ekre_and_ekcp["ekre"], "/v1/readiness").status_code == 200
    assert clients.get(ekre_and_ekcp["ekcp"], "/v1/readiness").status_code == 200


def test_ekre_retrieve_returns_citation_package(ekre_and_ekcp: dict[str, str]) -> None:
    response = clients.post_json(
        ekre_and_ekcp["ekre"],
        "/v1/query/retrieve",
        tenant_id=_TENANT,
        json={"query": "what is the data retention policy", "security_context": _SECURITY_CONTEXT},
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    assert "package" in body, f"expected a retrieval package, got keys {list(body)}"
    package = body["package"]
    assert package["tenant_id"] == _TENANT
    assert "candidates" in package


def test_ekcp_context_build_reaches_ekre_without_degradation(
    ekre_and_ekcp: dict[str, str],
) -> None:
    response = clients.post_json(
        ekre_and_ekcp["ekcp"],
        "/context/build",
        tenant_id=_TENANT,
        auth_token=EKCP_GATEWAY_TOKEN,
        json={
            "conversation_id": "conv-1",
            "user_intent": "what is the data retention policy",
            "security_context": _SECURITY_CONTEXT,
            "include_knowledge": True,
        },
    )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    assert body["degraded"] is False, f"EKCP degraded instead of reaching EKRE: {body}"


def test_ekcp_rejects_missing_gateway_token(ekre_and_ekcp: dict[str, str]) -> None:
    response = clients.post_json(
        ekre_and_ekcp["ekcp"],
        "/context/build",
        tenant_id=_TENANT,
        json={
            "conversation_id": "conv-1",
            "user_intent": "policy",
            "security_context": _SECURITY_CONTEXT,
            "include_knowledge": False,
        },
    )
    assert response.status_code == 401, response.text


def test_ekre_rejects_tenant_mismatch(ekre_and_ekcp: dict[str, str]) -> None:
    response = clients.post_json(
        ekre_and_ekcp["ekre"],
        "/v1/query/retrieve",
        tenant_id="tenant-other",
        json={"query": "policy", "security_context": _SECURITY_CONTEXT},
    )
    assert response.status_code == 403, response.text

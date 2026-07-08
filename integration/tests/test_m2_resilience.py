"""M2-S1: backpressure, circuit-breaking, and recovery.

Points EKCP at a controllable EKRE stub that returns HTTP 429 (backpressure) for
the first two calls, then a valid package. With a low circuit-breaker threshold
and a short reset, this exercises the full resilience arc: graceful degradation
on backpressure, an open circuit that sheds load without calling EKRE, and
automatic recovery once the dependency is healthy again.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest

from harness import clients
from harness.servers import EKCP_GATEWAY_TOKEN, ServiceHandle, launch_ekcp
from harness.stub_ekre import StubEkre

_TENANT = "tenant-a"
_SECURITY_CONTEXT = {
    "user_id": "u-1",
    "tenant_id": _TENANT,
    "classification_clearance": "internal",
}
_CB_THRESHOLD = 2
_CB_RESET_SECONDS = 3.0


@pytest.fixture(scope="module")
def ekcp_with_stub() -> Iterator[dict[str, Any]]:
    stub = StubEkre(failures_before_success=_CB_THRESHOLD).start()
    ekcp: ServiceHandle | None = None
    try:
        ekcp = launch_ekcp(
            port=18013,
            knowledge_base_url=stub.base_url,
            extra_env={
                "EKCP_KNOWLEDGE__CIRCUIT_BREAKER_THRESHOLD": str(_CB_THRESHOLD),
                "EKCP_KNOWLEDGE__CIRCUIT_BREAKER_RESET_SECONDS": str(_CB_RESET_SECONDS),
            },
        )
        yield {"ekcp": ekcp.base_url, "stub": stub}
    finally:
        if ekcp is not None:
            ekcp.stop()
        stub.stop()


def _build_context(base_url: str) -> dict[str, Any]:
    response = clients.post_json(
        base_url,
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
    return body


def _warnings(body: dict[str, Any]) -> str:
    return " ".join(body.get("warnings", []))


def test_backpressure_circuit_open_and_recovery(ekcp_with_stub: dict[str, Any]) -> None:
    base_url: str = ekcp_with_stub["ekcp"]
    stub: StubEkre = ekcp_with_stub["stub"]

    # Call 1: EKRE returns 429 -> graceful backpressure degradation.
    first = _build_context(base_url)
    assert first["degraded"] is True
    assert "backpressure" in _warnings(first)

    # Call 2: second 429 trips the circuit breaker open.
    second = _build_context(base_url)
    assert second["degraded"] is True
    assert "backpressure" in _warnings(second)

    # Call 3: circuit is open -> load shed without calling EKRE.
    hits_before = stub.hits
    third = _build_context(base_url)
    assert third["degraded"] is True
    assert "circuit_open" in _warnings(third)
    assert stub.hits == hits_before, "open circuit must not call EKRE"

    # After the reset window the circuit half-opens and the now-healthy stub
    # returns a package, closing the circuit and recovering.
    time.sleep(_CB_RESET_SECONDS + 0.3)
    recovered = _build_context(base_url)
    assert recovered["degraded"] is False, f"expected recovery, got {recovered}"
    assert stub.hits > hits_before, "recovery must call EKRE again"

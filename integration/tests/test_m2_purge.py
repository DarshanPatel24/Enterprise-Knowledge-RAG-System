"""M2-S2: DSAR purge propagation via the shared purge event contract.

Seeds a user's memory in EKCP, then drives an ``EnterpriseDataPurgeEvent`` through
the purge orchestrator and asserts the user's data is hard-deleted and no longer
retrievable. This demonstrates the contract-driven propagation pattern; the
orchestrator stands in for the cross-engine purge subscriber the platform needs.
"""

from __future__ import annotations

from typing import Any

from contracts import EnterpriseDataPurgeEvent

from harness import clients
from harness.purge import (
    PurgeOrchestrator,
    ekcp_memory_purge_adapter,
    ekie_document_purge_adapter,
)
from harness.servers import EKCP_GATEWAY_TOKEN

_TENANT = "tenant-a"
_USER = "dsar-user-1"
_SECURITY_CONTEXT = {
    "user_id": _USER,
    "tenant_id": _TENANT,
    "classification_clearance": "internal",
}


def _store_memory(base_url: str, content: str) -> None:
    response = clients.post_json(
        base_url,
        "/memory/store",
        tenant_id=_TENANT,
        auth_token=EKCP_GATEWAY_TOKEN,
        json={
            "security_context": _SECURITY_CONTEXT,
            "content": content,
            "scope": "user",
            "user_id": _USER,
        },
    )
    assert response.status_code == 200, response.text


def _retrieve_memory(base_url: str) -> list[dict[str, Any]]:
    response = clients.post_json(
        base_url,
        "/memory/retrieve",
        tenant_id=_TENANT,
        auth_token=EKCP_GATEWAY_TOKEN,
        json={
            "security_context": _SECURITY_CONTEXT,
            "query": "favorite",
            "scopes": ["user"],
            "min_confidence": 0.0,
        },
    )
    assert response.status_code == 200, response.text
    hits: list[dict[str, Any]] = response.json()["hits"]
    return hits


def test_dsar_purge_removes_user_memory(all_engines: dict[str, str]) -> None:
    ekcp = all_engines["ekcp"]
    ekie = all_engines["ekie"]

    _store_memory(ekcp, "favorite colour is blue")
    _store_memory(ekcp, "favorite food is pasta")
    assert len(_retrieve_memory(ekcp)) >= 2, "memory should be present before purge"

    event = EnterpriseDataPurgeEvent(
        user_id=_USER, tenant_id=_TENANT, correlation_id="dsar-corr-1", reason="gdpr_dsar"
    )
    orchestrator = PurgeOrchestrator(
        [
            ekcp_memory_purge_adapter(ekcp, auth_token=EKCP_GATEWAY_TOKEN),
            ekie_document_purge_adapter(ekie, document_ids=["dsar-doc-1"]),
        ]
    )
    results = {result.engine: result for result in orchestrator.purge(event)}

    assert results["ekcp"].status_code == 200, results["ekcp"]
    assert results["ekcp"].deleted_count is not None
    assert results["ekcp"].deleted_count >= 2
    assert _retrieve_memory(ekcp) == [], "user memory must be gone after purge"

    # EKIE participates in the fan-out; the subject's document set is supplied by
    # the subscriber (EKIE has no user attribution). The batch purge is idempotent.
    assert results["ekie"].status_code == 200, results["ekie"]
    assert results["ekie"].deleted_count == 0

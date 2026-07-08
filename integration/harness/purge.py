"""DSAR purge propagation driven by the shared ``EnterpriseDataPurgeEvent``.

A GDPR/DSAR purge is a cross-engine concern: the canonical purge event is fanned
out to each engine's purge surface. This orchestrator is the propagation
mechanism the platform lacks today (engines each purge locally but do not
subscribe to a shared event bus). EKCP exposes a user-scoped memory purge; EKIE
currently exposes only per-document deletion (recorded as a gap).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from contracts import EnterpriseDataPurgeEvent

from harness import clients


@dataclass(frozen=True)
class PurgeResult:
    """Outcome of purging one engine for a DSAR event."""

    engine: str
    status_code: int
    deleted_count: int | None


PurgeAdapter = Callable[[EnterpriseDataPurgeEvent], PurgeResult]


def ekcp_memory_purge_adapter(
    base_url: str, *, auth_token: str, clearance: str = "internal"
) -> PurgeAdapter:
    """Build an adapter that purges a user's EKCP memory for a DSAR event."""

    def _adapter(event: EnterpriseDataPurgeEvent) -> PurgeResult:
        response = clients.post_json(
            base_url,
            "/memory/purge",
            tenant_id=event.tenant_id,
            auth_token=auth_token,
            correlation_id=event.correlation_id,
            json={
                "security_context": {
                    "user_id": event.user_id,
                    "tenant_id": event.tenant_id,
                    "classification_clearance": clearance,
                },
                "user_id": event.user_id,
                "reason": event.reason or "dsar_purge",
            },
        )
        deleted = (
            int(response.json().get("deleted_count", 0))
            if response.status_code == 200
            else None
        )
        return PurgeResult("ekcp", response.status_code, deleted)

    return _adapter


def ekie_document_purge_adapter(
    base_url: str, *, document_ids: list[str]
) -> PurgeAdapter:
    """Build an adapter that purges a subject's EKIE documents for a DSAR event.

    EKIE data is scoped by tenant and document (no user attribution), so the DSAR
    subscriber resolves the subject's document set upstream and passes it here; the
    adapter invokes EKIE's batch purge endpoint with the tenant from the event.
    """

    def _adapter(event: EnterpriseDataPurgeEvent) -> PurgeResult:
        response = clients.post_json(
            base_url,
            "/v1/documents/purge",
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            json={"document_ids": document_ids, "reason": event.reason or "dsar_purge"},
        )
        deleted = (
            int(response.json().get("deleted_count", 0))
            if response.status_code == 200
            else None
        )
        return PurgeResult("ekie", response.status_code, deleted)

    return _adapter


class PurgeOrchestrator:
    """Fan a single ``EnterpriseDataPurgeEvent`` out to every engine adapter."""

    def __init__(self, adapters: list[PurgeAdapter]) -> None:
        self._adapters = adapters

    def purge(self, event: EnterpriseDataPurgeEvent) -> list[PurgeResult]:
        return [adapter(event) for adapter in self._adapters]

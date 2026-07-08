"""Persistent audit sink and inbound PII masking tests (security review closure)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import build_resources, get_resources
from composition import build_governance_guard
from config.settings import EkcpSettings
from domain.governance import AuditAction, FileAuditSink

_CONTEXT = {
    "user_id": "u1",
    "tenant_id": "tenant-a",
    "classification_clearance": "internal",
}


def _guard_settings(**governance: object) -> EkcpSettings:
    return EkcpSettings(_env_file=None, governance=governance)  # type: ignore[arg-type]


def test_file_audit_sink_round_trip(tmp_path: Path) -> None:
    path = str(tmp_path / "audit.jsonl")
    guard = build_governance_guard(
        _guard_settings(audit_sink="file", audit_file_path=path)
    )
    guard.sanitize_input(
        "reach me at a@b.com", actor="u1", tenant_id="tenant-a", resource="memory"
    )
    history = guard.audit_sink.history(tenant_id="tenant-a")  # type: ignore[attr-defined]
    assert len(history) == 1
    assert history[0].action == AuditAction.INPUT_FILTERED


def test_file_audit_sink_is_durable(tmp_path: Path) -> None:
    path = str(tmp_path / "audit.jsonl")
    guard = build_governance_guard(
        _guard_settings(audit_sink="file", audit_file_path=path)
    )
    guard.sanitize_input("a@b.com", actor="u1", tenant_id="tenant-a")
    # A fresh sink reading the same file recovers the persisted trail.
    reopened = FileAuditSink(path)
    assert len(reopened.history()) == 1


def test_inbound_masking_redacts_pii() -> None:
    guard = build_governance_guard(_guard_settings(mask_inbound=True))
    masked, count = guard.sanitize_input(
        "ssn 123-45-6789", actor="u1", tenant_id="tenant-a"
    )
    assert count == 1
    assert "[REDACTED-SSN]" in masked
    assert "123-45-6789" not in masked


def test_inbound_masking_can_be_disabled() -> None:
    guard = build_governance_guard(_guard_settings(mask_inbound=False))
    masked, count = guard.sanitize_input("a@b.com", actor="u1", tenant_id="tenant-a")
    assert count == 0
    assert masked == "a@b.com"


def _client(settings: EkcpSettings) -> AsyncClient:
    app = create_app(settings)
    resources = build_resources(settings)
    app.dependency_overrides[get_resources] = lambda: resources
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://ekcp.test")


@pytest.fixture
def settings() -> EkcpSettings:
    return EkcpSettings(_env_file=None)


async def test_memory_store_masks_inbound_pii(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        stored = await client.post(
            "/memory/store",
            headers={"X-Tenant-ID": "tenant-a"},
            json={
                "security_context": _CONTEXT,
                "content": "contact me at jane@example.com",
                "topic": "contact",
            },
        )
        assert stored.status_code == httpx.codes.OK
        retrieved = await client.post(
            "/memory/retrieve",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"security_context": _CONTEXT, "query": "contact"},
        )
    assert retrieved.status_code == httpx.codes.OK
    hits = retrieved.json()["hits"]
    assert hits
    assert "jane@example.com" not in hits[0]["content"]
    assert "[REDACTED-EMAIL]" in hits[0]["content"]

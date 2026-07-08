"""Tests for the security audit trail."""

from __future__ import annotations

from domain.governance import (
    AuditAction,
    AuditResult,
    InMemoryAuditSink,
    build_audit_record,
)


def test_audit_record_has_id_and_timestamp() -> None:
    record = build_audit_record(
        action=AuditAction.RETRIEVE,
        result=AuditResult.ALLOWED,
        actor="analyst-1",
        tenant_id="tenant-a",
        execution_id="exec-1",
    )
    assert record.event_id.startswith("audit-")
    assert record.timestamp is not None
    assert record.action is AuditAction.RETRIEVE


def test_in_memory_sink_is_append_only() -> None:
    sink = InMemoryAuditSink()
    sink.record(
        build_audit_record(
            action=AuditAction.RETRIEVE,
            result=AuditResult.ALLOWED,
            actor="u",
            tenant_id="t",
            execution_id="e1",
        )
    )
    sink.record(
        build_audit_record(
            action=AuditAction.ACCESS_DENIED,
            result=AuditResult.DENIED,
            actor="u",
            tenant_id="t",
            execution_id="e2",
        )
    )
    history = sink.history()
    assert len(history) == 2
    assert history[0].result is AuditResult.ALLOWED
    assert history[1].result is AuditResult.DENIED


def test_record_access_denied_writes_denied_record(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import composition
    from config.settings import EkreSettings

    sink = InMemoryAuditSink()
    monkeypatch.setattr(composition, "build_audit_sink", lambda settings: sink)
    composition.record_access_denied(
        EkreSettings(_env_file=None),
        actor="u1",
        tenant_id="tenant-a",
        reason="tenant_mismatch",
    )
    history = sink.history()
    assert len(history) == 1
    assert history[0].action is AuditAction.ACCESS_DENIED
    assert history[0].result is AuditResult.DENIED
    assert history[0].detail["reason"] == "tenant_mismatch"


def test_record_access_denied_respects_disabled_audit(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import composition
    from config.settings import EkreSettings

    sink = InMemoryAuditSink()
    monkeypatch.setattr(composition, "build_audit_sink", lambda settings: sink)
    settings = EkreSettings(_env_file=None)
    disabled = settings.model_copy(
        update={"governance": settings.governance.model_copy(update={"enable_audit": False})}
    )
    composition.record_access_denied(
        disabled, actor="u1", tenant_id="tenant-a", reason="tenant_mismatch"
    )
    assert sink.history() == ()

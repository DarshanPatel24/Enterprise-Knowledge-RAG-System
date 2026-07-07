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

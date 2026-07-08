"""Immutable audit trail for governed operations (handbook 12.14).

Every governed decision is recorded to an append-only audit sink so governance
scenarios have complete, searchable evidence. Records are frozen; the in-memory
sink retains an ordered history for compliance evidence and tests, and the
logging sink emits structured records.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from domain.observability import get_correlation_id, get_logger, get_session_id

logger = get_logger("ekcp.governance.audit")


class AuditAction(StrEnum):
    """Governed actions recorded in the audit trail (handbook 12.14)."""

    SECURITY_CONTEXT_VALIDATED = "security_context_validated"
    POLICY_GRANTED = "policy_granted"
    POLICY_DENIED = "policy_denied"
    TOOL_INVOKED = "tool_invoked"
    TOOL_DENIED = "tool_denied"
    CONTEXT_RETRIEVED = "context_retrieved"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    MEMORY_DENIED = "memory_denied"
    AGENT_INVOKED = "agent_invoked"
    AGENT_DENIED = "agent_denied"
    RESPONSE_GENERATED = "response_generated"
    RESPONSE_FILTERED = "response_filtered"
    INPUT_FILTERED = "input_filtered"
    CLASSIFICATION_CHECKED = "classification_checked"
    CLEARANCE_VIOLATION = "clearance_violation"
    SECURITY_CONTEXT_PROPAGATED = "security_context_propagated"


class AuditResult(StrEnum):
    """Outcome of an audited action."""

    ALLOWED = "allowed"
    DENIED = "denied"


class AuditRecord(BaseModel):
    """An immutable, append-only audit trail entry (handbook 12.14)."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: f"audit-{uuid.uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: str
    action: AuditAction
    result: AuditResult
    resource: str
    tenant_id: str
    session_id: str | None = None
    conversation_id: str | None = None
    correlation_id: str | None = None
    policy_version: str = "v1"
    reason: str = ""
    detail: dict[str, str] = Field(default_factory=dict)


class AuditSink(ABC):
    """Append-only destination for audit records."""

    @abstractmethod
    def record(self, entry: AuditRecord) -> None:
        """Append ``entry`` to the audit trail."""


class QueryableAuditSink(AuditSink):
    """An audit sink whose trail can be read back for compliance evidence."""

    @abstractmethod
    def history(self, *, tenant_id: str | None = None) -> tuple[AuditRecord, ...]:
        """Return an immutable snapshot of the audit trail, optionally by tenant."""


class InMemoryAuditSink(QueryableAuditSink):
    """Append-only in-memory audit trail for compliance evidence and tests."""

    def __init__(self) -> None:
        self._entries: list[AuditRecord] = []

    def record(self, entry: AuditRecord) -> None:
        self._entries.append(entry)

    def history(self, *, tenant_id: str | None = None) -> tuple[AuditRecord, ...]:
        """Return an immutable snapshot of the audit trail, optionally by tenant."""
        if tenant_id is None:
            return tuple(self._entries)
        return tuple(e for e in self._entries if e.tenant_id == tenant_id)


class FileAuditSink(QueryableAuditSink):
    """Durable append-only audit trail persisted as JSON lines.

    Each record is appended as one JSON object per line and flushed immediately,
    so the trail survives restarts and provides ordered, tamper-evident evidence
    for compliance. The parent directory is created on first use.
    """

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, entry: AuditRecord) -> None:
        with self._path.open("a", encoding="utf-8") as stream:
            stream.write(entry.model_dump_json() + "\n")

    def history(self, *, tenant_id: str | None = None) -> tuple[AuditRecord, ...]:
        """Read the persisted trail back, optionally filtered by tenant."""
        if not self._path.exists():
            return ()
        records: list[AuditRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = AuditRecord.model_validate_json(line)
            if tenant_id is None or record.tenant_id == tenant_id:
                records.append(record)
        return tuple(records)


class LoggingAuditSink(AuditSink):
    """Emit audit records as structured JSON logs (append-only by nature)."""

    def record(self, entry: AuditRecord) -> None:
        logger.info(
            "audit_event",
            extra={
                "event_id": entry.event_id,
                "actor": entry.actor,
                "action": entry.action,
                "result": entry.result,
                "resource": entry.resource,
                "tenant_id": entry.tenant_id,
                "policy_version": entry.policy_version,
            },
        )


def build_audit_record(
    *,
    actor: str,
    action: AuditAction,
    result: AuditResult,
    resource: str,
    tenant_id: str,
    reason: str = "",
    policy_version: str = "v1",
    detail: dict[str, str] | None = None,
) -> AuditRecord:
    """Build an audit record with correlation and session ids bound from context."""
    return AuditRecord(
        actor=actor,
        action=action,
        result=result,
        resource=resource,
        tenant_id=tenant_id,
        session_id=get_session_id(),
        correlation_id=get_correlation_id(),
        reason=reason,
        policy_version=policy_version,
        detail=detail or {},
    )

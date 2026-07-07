"""Immutable security audit trail (handbook Chapter 29.12).

Every security-relevant retrieval decision is recorded as an immutable audit
record. Sinks persist records to structured logs or to memory (for tests). The
audit trail observes decisions; it never influences execution.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from domain.observability import get_logger

_logger = get_logger("ekre.audit")


class AuditAction(StrEnum):
    """Security-relevant actions that are audited."""

    RETRIEVE = "retrieve"
    ACCESS_DENIED = "access_denied"
    MASK_APPLIED = "mask_applied"


class AuditResult(StrEnum):
    """Outcome of an audited decision."""

    ALLOWED = "allowed"
    DENIED = "denied"


class AuditRecord(BaseModel):
    """An immutable record of one security decision (handbook 29.12)."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(min_length=1)
    timestamp: datetime
    action: AuditAction
    result: AuditResult
    actor: str
    tenant_id: str
    execution_id: str
    correlation_id: str | None = None
    policy_version: str = "v1"
    detail: dict[str, str] = Field(default_factory=dict)


def build_audit_record(
    *,
    action: AuditAction,
    result: AuditResult,
    actor: str,
    tenant_id: str,
    execution_id: str,
    correlation_id: str | None = None,
    policy_version: str = "v1",
    detail: dict[str, str] | None = None,
) -> AuditRecord:
    """Construct an audit record with a fresh id and UTC timestamp."""
    return AuditRecord(
        event_id=f"audit-{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(UTC),
        action=action,
        result=result,
        actor=actor,
        tenant_id=tenant_id,
        execution_id=execution_id,
        correlation_id=correlation_id,
        policy_version=policy_version,
        detail=detail or {},
    )


class AuditSink(ABC):
    """Persists immutable audit records."""

    @abstractmethod
    def record(self, record: AuditRecord) -> None:
        """Append an audit record to the trail."""


class InMemoryAuditSink(AuditSink):
    """In-process append-only audit sink for tests and offline use."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def record(self, record: AuditRecord) -> None:
        """Append the record to the in-memory trail."""
        self._records.append(record)

    def history(self) -> tuple[AuditRecord, ...]:
        """Return the append-only audit history."""
        return tuple(self._records)


class LoggingAuditSink(AuditSink):
    """Emits audit records as structured logs."""

    def record(self, record: AuditRecord) -> None:
        """Emit the record as a structured log line."""
        _logger.info(
            "audit_event",
            extra={
                "event_id": record.event_id,
                "action": record.action.value,
                "result": record.result.value,
                "actor": record.actor,
                "execution_id": record.execution_id,
                "policy_version": record.policy_version,
            },
        )

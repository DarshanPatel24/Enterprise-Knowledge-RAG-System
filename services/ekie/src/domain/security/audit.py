"""Append-only audit logging for governance evidence (handbook 17.10).

Every governed action produces an immutable :class:`AuditRecord`. Sinks are
append-only: the in-memory sink retains an ordered, read-only history and the
logging sink emits structured records enriched with tenant and correlation
context. Audit records never carry secret values.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from domain.observability import get_logger

_logger = get_logger("ekie.security.audit")


class AuditAction(StrEnum):
    """Governed actions recorded in the audit trail (handbook 17.10)."""

    DOCUMENT_INGESTED = "document_ingested"
    STAGE_AUTHORIZED = "stage_authorized"
    STAGE_DENIED = "stage_denied"
    CLASSIFICATION_PROPAGATED = "classification_propagated"
    CLASSIFICATION_VIOLATION = "classification_violation"
    PLUGIN_VALIDATED = "plugin_validated"
    PLUGIN_REJECTED = "plugin_rejected"
    PLUGIN_ACTIVATED = "plugin_activated"


class AuditResult(StrEnum):
    """Outcome of an audited action."""

    ALLOW = "allow"
    DENY = "deny"


class AuditRecord(BaseModel):
    """An immutable, append-only audit trail entry (handbook 17.10)."""

    model_config = {"frozen": True}

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: str
    action: AuditAction
    resource: str
    result: AuditResult
    tenant_id: str | None = None
    correlation_id: str | None = None
    detail: str = ""


class AuditSink(ABC):
    """Append-only destination for audit records."""

    @abstractmethod
    def record(self, entry: AuditRecord) -> None:
        """Append ``entry`` to the audit trail."""


class InMemoryAuditSink(AuditSink):
    """Append-only in-memory audit trail for tests and local evidence."""

    def __init__(self) -> None:
        self._entries: list[AuditRecord] = []

    def record(self, entry: AuditRecord) -> None:
        """Append ``entry`` to the ordered history."""
        self._entries.append(entry)

    def history(self) -> tuple[AuditRecord, ...]:
        """Return an immutable snapshot of the audit trail."""
        return tuple(self._entries)


class LoggingAuditSink(AuditSink):
    """Emit audit records as structured JSON logs (append-only by nature)."""

    def record(self, entry: AuditRecord) -> None:
        """Emit ``entry`` through the structured logger."""
        _logger.info(
            "audit_event",
            extra={
                "event_id": entry.event_id,
                "actor": entry.actor,
                "action": entry.action.value,
                "resource": entry.resource,
                "result": entry.result.value,
                "audit_detail": entry.detail,
            },
        )

"""Standardized synchronization events (EKIE handbook Chapter 6.19).

These events are internal to EKIE and feed the Workflow Engine. They are not
cross-engine payloads, so they live in the EKIE domain rather than in
packages/contracts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SyncEventType(StrEnum):
    """The set of events emitted by repository synchronization."""

    REPOSITORY_SYNCHRONIZED = "RepositorySynchronized"
    REPOSITORY_RECONCILED = "RepositoryReconciled"
    DOCUMENT_DISCOVERED = "DocumentDiscovered"
    DOCUMENT_MODIFIED = "DocumentModified"
    DOCUMENT_RENAMED = "DocumentRenamed"
    DOCUMENT_MOVED = "DocumentMoved"
    DOCUMENT_DELETED = "DocumentDeleted"
    SYNCHRONIZATION_FAILED = "SynchronizationFailed"


class SyncEvent(BaseModel):
    """A single normalized synchronization event."""

    model_config = {"frozen": True}

    event_type: SyncEventType
    repository_id: str
    tenant_id: str
    document_id: str | None = None
    source_path: str | None = None
    previous_path: str | None = None
    version: int | None = None
    detail: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

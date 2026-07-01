"""Execution context contract shared across all engines."""

from datetime import UTC, datetime

from pydantic import Field

from contracts.base import VersionedContract


class ExecutionContext(VersionedContract):
    """Correlation and tenancy metadata attached to every cross-service call."""

    request_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    session_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

"""Global governance events subscribed to by all engines."""

from datetime import UTC, datetime

from pydantic import Field

from contracts.base import VersionedContract


class EnterpriseDataPurgeEvent(VersionedContract):
    """GDPR/DSAR purge event requiring hard deletion of a user's data."""

    user_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reason: str | None = None

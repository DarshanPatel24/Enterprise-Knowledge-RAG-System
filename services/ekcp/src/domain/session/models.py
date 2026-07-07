"""Session model.

A session represents an authenticated access channel for a user. A user may hold
several concurrent sessions (different devices) that all reach the same
conversation; session expiration never terminates a conversation. Sessions are
immutable; updates produce a new session via ``model_copy``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class Session(BaseModel):
    """Immutable authenticated session bound to a user and tenant."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    user_id: str
    tenant_id: str
    locale: str = "en"
    active_conversation_ref: str | None = None
    device_info: str = ""
    version_number: int = 0
    created_at: datetime = Field(default_factory=_utc_now)
    last_activity: datetime = Field(default_factory=_utc_now)
    expires_at: datetime = Field(default_factory=_utc_now)

    def is_expired(self, *, now: datetime | None = None) -> bool:
        """Return whether the session has passed its expiration time."""
        return (now or _utc_now()) >= self.expires_at

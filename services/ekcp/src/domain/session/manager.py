"""Session administration: create, load, touch, and attach conversations.

The manager owns session identity and the expiration policy. Touching a session
extends its expiration window; expired sessions are rejected on load so callers
can transparently re-authenticate without affecting the conversation.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from domain.session.errors import SessionError, SessionErrorType
from domain.session.models import Session
from domain.session.store import SessionStore


def _new_session_id() -> str:
    """Return a fresh globally-unique session id."""
    return f"sess-{uuid.uuid4().hex[:12]}"


class SessionManager:
    """Create and maintain authenticated sessions with an expiration policy."""

    def __init__(
        self,
        store: SessionStore,
        *,
        session_ttl_seconds: float,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._ttl = timedelta(seconds=session_ttl_seconds)
        self._clock = clock or (lambda: datetime.now(UTC))

    def create(
        self,
        *,
        tenant_id: str,
        user_id: str,
        locale: str = "en",
        device_info: str = "",
        active_conversation_ref: str | None = None,
    ) -> Session:
        """Create a new session and persist it."""
        now = self._clock()
        session = Session(
            session_id=_new_session_id(),
            user_id=user_id,
            tenant_id=tenant_id,
            locale=locale,
            device_info=device_info,
            active_conversation_ref=active_conversation_ref,
            created_at=now,
            last_activity=now,
            expires_at=now + self._ttl,
        )
        self._store.save(session, expected_version=None)
        return session

    def get(self, tenant_id: str, session_id: str) -> Session:
        """Return an active session, or raise ``EXPIRED`` when past expiration."""
        session = self._store.get(tenant_id, session_id)
        if session.is_expired(now=self._clock()):
            raise SessionError(
                SessionErrorType.EXPIRED, f"session {session_id} has expired"
            )
        return session

    def touch(self, tenant_id: str, session_id: str) -> Session:
        """Extend a session's expiration window and record activity."""
        session = self.get(tenant_id, session_id)
        now = self._clock()
        updated = session.model_copy(
            update={
                "last_activity": now,
                "expires_at": now + self._ttl,
                "version_number": session.version_number + 1,
            }
        )
        self._store.save(updated, expected_version=session.version_number)
        return updated

    def attach_conversation(
        self, tenant_id: str, session_id: str, conversation_id: str
    ) -> Session:
        """Bind a conversation as the session's active conversation."""
        session = self.get(tenant_id, session_id)
        updated = session.model_copy(
            update={
                "active_conversation_ref": conversation_id,
                "last_activity": self._clock(),
                "version_number": session.version_number + 1,
            }
        )
        self._store.save(updated, expected_version=session.version_number)
        return updated

"""Session persistence with optimistic concurrency.

The store persists immutable sessions keyed by ``(tenant_id, session_id)`` and
guards saves with the expected version so concurrent updates cannot silently
overwrite each other. The in-memory store is the local-first offline default;
Redis is wired behind the same interface later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.session.errors import SessionError, SessionErrorType
from domain.session.models import Session


class SessionStore(ABC):
    """Abstract session persistence keyed by tenant and session id."""

    @abstractmethod
    def get(self, tenant_id: str, session_id: str) -> Session:
        """Return the stored session, or raise ``NOT_FOUND``."""

    @abstractmethod
    def save(self, session: Session, *, expected_version: int | None) -> None:
        """Persist ``session`` guarded by ``expected_version`` (None for create)."""


class InMemorySessionStore(SessionStore):
    """Deterministic in-memory session store (local-first default)."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Session] = {}

    def get(self, tenant_id: str, session_id: str) -> Session:
        session = self._items.get((tenant_id, session_id))
        if session is None:
            raise SessionError(
                SessionErrorType.NOT_FOUND,
                f"session {session_id} not found for tenant {tenant_id}",
            )
        return session

    def save(self, session: Session, *, expected_version: int | None) -> None:
        key = (session.tenant_id, session.session_id)
        existing = self._items.get(key)
        if expected_version is None:
            if existing is not None:
                raise SessionError(
                    SessionErrorType.ALREADY_EXISTS,
                    f"session {session.session_id} already exists",
                )
        else:
            if existing is None:
                raise SessionError(
                    SessionErrorType.NOT_FOUND, f"session {session.session_id} not found"
                )
            if existing.version_number != expected_version:
                raise SessionError(
                    SessionErrorType.VERSION_CONFLICT,
                    (
                        f"version conflict for {session.session_id}: "
                        f"expected {expected_version}, found {existing.version_number}"
                    ),
                )
        self._items[key] = session

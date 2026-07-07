"""Tests for session management: creation, expiration, and concurrency."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from domain.session import (
    InMemorySessionStore,
    SessionError,
    SessionErrorType,
    SessionManager,
)


class _Clock:
    """Manually advanced clock for deterministic expiration tests."""

    def __init__(self) -> None:
        self._now = datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


def test_create_and_get_session() -> None:
    manager = SessionManager(InMemorySessionStore(), session_ttl_seconds=3600.0)
    session = manager.create(tenant_id="tenant-a", user_id="analyst-1")
    loaded = manager.get("tenant-a", session.session_id)
    assert loaded.session_id == session.session_id
    assert loaded.user_id == "analyst-1"


def test_expired_session_rejected() -> None:
    clock = _Clock()
    manager = SessionManager(
        InMemorySessionStore(), session_ttl_seconds=60.0, clock=clock
    )
    session = manager.create(tenant_id="tenant-a", user_id="analyst-1")
    clock.advance(120.0)
    with pytest.raises(SessionError) as exc:
        manager.get("tenant-a", session.session_id)
    assert exc.value.error_type == SessionErrorType.EXPIRED


def test_touch_extends_expiration() -> None:
    clock = _Clock()
    manager = SessionManager(
        InMemorySessionStore(), session_ttl_seconds=60.0, clock=clock
    )
    session = manager.create(tenant_id="tenant-a", user_id="analyst-1")
    clock.advance(30.0)
    touched = manager.touch("tenant-a", session.session_id)
    assert touched.version_number == session.version_number + 1
    clock.advance(45.0)
    # Still valid because touch reset the 60s window at t=30.
    assert manager.get("tenant-a", session.session_id).session_id == session.session_id


def test_attach_conversation() -> None:
    manager = SessionManager(InMemorySessionStore(), session_ttl_seconds=3600.0)
    session = manager.create(tenant_id="tenant-a", user_id="analyst-1")
    updated = manager.attach_conversation("tenant-a", session.session_id, "conv-9")
    assert updated.active_conversation_ref == "conv-9"

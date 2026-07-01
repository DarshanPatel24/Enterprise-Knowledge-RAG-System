"""Repository and document synchronization state machines.

Encodes the lifecycles from EKIE handbook Chapters 6.17 and 6.18 and validates
transitions so the Digital Twin can never enter an inconsistent state.
"""

from __future__ import annotations

from enum import StrEnum


class RepositorySyncState(StrEnum):
    """Repository synchronization lifecycle states (handbook 6.17)."""

    REGISTERED = "registered"
    CONNECTING = "connecting"
    DISCOVERING = "discovering"
    SYNCHRONIZING = "synchronizing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    RECONCILING = "reconciling"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class DocumentSyncState(StrEnum):
    """Document synchronization lifecycle states (handbook 6.18)."""

    NEW = "new"
    DISCOVERED = "discovered"
    HASH_VERIFIED = "hash_verified"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    RENAMED = "renamed"
    MOVED = "moved"
    DELETED = "deleted"
    FAILED = "failed"
    WAITING = "waiting"
    WORKFLOW_CREATED = "workflow_created"


class InvalidStateTransitionError(RuntimeError):
    """Raised when a state transition is not permitted."""


_REPOSITORY_TRANSITIONS: frozenset[tuple[RepositorySyncState, RepositorySyncState]] = frozenset(
    {
        (RepositorySyncState.REGISTERED, RepositorySyncState.CONNECTING),
        (RepositorySyncState.CONNECTING, RepositorySyncState.DISCOVERING),
        (RepositorySyncState.CONNECTING, RepositorySyncState.ERROR),
        (RepositorySyncState.DISCOVERING, RepositorySyncState.SYNCHRONIZING),
        (RepositorySyncState.DISCOVERING, RepositorySyncState.ERROR),
        (RepositorySyncState.SYNCHRONIZING, RepositorySyncState.ACTIVE),
        (RepositorySyncState.SYNCHRONIZING, RepositorySyncState.ERROR),
        (RepositorySyncState.ACTIVE, RepositorySyncState.SYNCHRONIZING),
        (RepositorySyncState.ACTIVE, RepositorySyncState.RECONCILING),
        (RepositorySyncState.ACTIVE, RepositorySyncState.PAUSED),
        (RepositorySyncState.ACTIVE, RepositorySyncState.DISABLED),
        (RepositorySyncState.RECONCILING, RepositorySyncState.ACTIVE),
        (RepositorySyncState.RECONCILING, RepositorySyncState.ERROR),
        (RepositorySyncState.PAUSED, RepositorySyncState.ACTIVE),
        (RepositorySyncState.PAUSED, RepositorySyncState.DISABLED),
        (RepositorySyncState.ERROR, RepositorySyncState.CONNECTING),
        (RepositorySyncState.ERROR, RepositorySyncState.DISABLED),
        (RepositorySyncState.DISABLED, RepositorySyncState.ARCHIVED),
        (RepositorySyncState.DISABLED, RepositorySyncState.REGISTERED),
    }
)

_DOCUMENT_TRANSITIONS: frozenset[tuple[DocumentSyncState, DocumentSyncState]] = frozenset(
    {
        (DocumentSyncState.NEW, DocumentSyncState.DISCOVERED),
        (DocumentSyncState.DISCOVERED, DocumentSyncState.HASH_VERIFIED),
        (DocumentSyncState.HASH_VERIFIED, DocumentSyncState.UNCHANGED),
        (DocumentSyncState.HASH_VERIFIED, DocumentSyncState.CHANGED),
        (DocumentSyncState.HASH_VERIFIED, DocumentSyncState.RENAMED),
        (DocumentSyncState.HASH_VERIFIED, DocumentSyncState.MOVED),
        (DocumentSyncState.CHANGED, DocumentSyncState.WORKFLOW_CREATED),
        (DocumentSyncState.RENAMED, DocumentSyncState.UNCHANGED),
        (DocumentSyncState.MOVED, DocumentSyncState.UNCHANGED),
        (DocumentSyncState.UNCHANGED, DocumentSyncState.CHANGED),
        (DocumentSyncState.UNCHANGED, DocumentSyncState.RENAMED),
        (DocumentSyncState.UNCHANGED, DocumentSyncState.MOVED),
        (DocumentSyncState.UNCHANGED, DocumentSyncState.DELETED),
        (DocumentSyncState.CHANGED, DocumentSyncState.DELETED),
        (DocumentSyncState.WORKFLOW_CREATED, DocumentSyncState.UNCHANGED),
        (DocumentSyncState.WORKFLOW_CREATED, DocumentSyncState.FAILED),
        (DocumentSyncState.FAILED, DocumentSyncState.WAITING),
        (DocumentSyncState.WAITING, DocumentSyncState.HASH_VERIFIED),
    }
)


def can_transition_repository(
    current: RepositorySyncState, target: RepositorySyncState
) -> bool:
    """Return whether a repository transition is permitted."""
    return (current, target) in _REPOSITORY_TRANSITIONS


def assert_repository_transition(
    current: RepositorySyncState, target: RepositorySyncState
) -> None:
    """Raise if a repository transition is not permitted."""
    if not can_transition_repository(current, target):
        raise InvalidStateTransitionError(
            f"invalid repository transition: {current} -> {target}"
        )


def can_transition_document(
    current: DocumentSyncState, target: DocumentSyncState
) -> bool:
    """Return whether a document transition is permitted."""
    return (current, target) in _DOCUMENT_TRANSITIONS


def assert_document_transition(
    current: DocumentSyncState, target: DocumentSyncState
) -> None:
    """Raise if a document transition is not permitted."""
    if not can_transition_document(current, target):
        raise InvalidStateTransitionError(
            f"invalid document transition: {current} -> {target}"
        )

"""Tests for synchronization state machines, policy, and retry."""

import pytest

from domain.sync.policy import ScanStrategy, SyncPolicy
from domain.sync.retry import RetryPolicy, run_with_retry
from domain.sync.state_machine import (
    DocumentSyncState,
    InvalidStateTransitionError,
    RepositorySyncState,
    assert_document_transition,
    assert_repository_transition,
    can_transition_repository,
)


def test_repository_valid_transition() -> None:
    assert can_transition_repository(
        RepositorySyncState.REGISTERED, RepositorySyncState.CONNECTING
    )
    assert_repository_transition(RepositorySyncState.CONNECTING, RepositorySyncState.DISCOVERING)


def test_repository_invalid_transition_raises() -> None:
    with pytest.raises(InvalidStateTransitionError):
        assert_repository_transition(RepositorySyncState.REGISTERED, RepositorySyncState.ACTIVE)


def test_document_transition_rename_returns_to_unchanged() -> None:
    assert_document_transition(DocumentSyncState.HASH_VERIFIED, DocumentSyncState.RENAMED)
    assert_document_transition(DocumentSyncState.RENAMED, DocumentSyncState.UNCHANGED)


def test_document_invalid_transition_raises() -> None:
    with pytest.raises(InvalidStateTransitionError):
        assert_document_transition(DocumentSyncState.NEW, DocumentSyncState.DELETED)


def test_policy_filters_hidden_and_extension_and_size() -> None:
    policy = SyncPolicy(allowed_extensions=frozenset({"pdf"}), max_file_size_bytes=100)
    assert policy.is_included(extension="pdf", size_bytes=50, is_hidden=False, name="a.pdf")
    assert not policy.is_included(extension="pdf", size_bytes=50, is_hidden=True, name=".a.pdf")
    assert not policy.is_included(extension="txt", size_bytes=50, is_hidden=False, name="a.txt")
    assert not policy.is_included(extension="pdf", size_bytes=200, is_hidden=False, name="a.pdf")


def test_policy_temp_files_excluded() -> None:
    policy = SyncPolicy()
    assert not policy.is_included(extension="tmp", size_bytes=1, is_hidden=False, name="a.tmp")
    assert not policy.is_included(extension="docx", size_bytes=1, is_hidden=False, name="~$a.docx")


def test_retry_succeeds_after_transient_failures() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectorFailure("transient")
        return "ok"

    result = run_with_retry(
        flaky,
        policy=RetryPolicy(max_attempts=3, backoff_base_seconds=0.0),
        retryable=ConnectorFailure,
        sleep=lambda _seconds: None,
    )
    assert result == "ok"
    assert calls["n"] == 3


def test_retry_reraises_after_exhausting_attempts() -> None:
    def always_fail() -> str:
        raise ConnectorFailure("permanent")

    with pytest.raises(ConnectorFailure):
        run_with_retry(
            always_fail,
            policy=RetryPolicy(max_attempts=2, backoff_base_seconds=0.0),
            retryable=ConnectorFailure,
            sleep=lambda _seconds: None,
        )


def test_default_scan_strategy_is_incremental() -> None:
    assert SyncPolicy().scan_strategy is ScanStrategy.INCREMENTAL


class ConnectorFailure(Exception):
    """Local test exception for retry behavior."""

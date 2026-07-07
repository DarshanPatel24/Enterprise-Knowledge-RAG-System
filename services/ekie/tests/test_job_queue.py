"""Tests for the durable ingestion job queue (:class:`JobQueueStore`)."""

from __future__ import annotations

from domain.control_plane import ControlPlaneDatabase, JobKind, JobStatus
from domain.jobs import JobQueueStore

_TENANT = "tenant-q"


def _store(db: ControlPlaneDatabase) -> JobQueueStore:
    return JobQueueStore(db)


def test_enqueue_creates_queued_job(control_plane_db: ControlPlaneDatabase) -> None:
    store = _store(control_plane_db)
    job_id = store.enqueue(
        tenant_id=_TENANT,
        document_id="doc-1",
        kind=JobKind.INGEST,
        content_hash="h1",
        source_path="a.md",
    )
    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.QUEUED
    assert record.kind is JobKind.INGEST
    assert record.attempts == 0


def test_enqueue_dedupes_active_jobs(control_plane_db: ControlPlaneDatabase) -> None:
    store = _store(control_plane_db)
    first = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, content_hash="h1"
    )
    second = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, content_hash="h1"
    )
    assert first == second
    # A different content hash is a distinct job.
    third = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, content_hash="h2"
    )
    assert third != first


def test_claim_locks_job_and_is_exclusive(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    store = _store(control_plane_db)
    store.enqueue(tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST)

    claimed = store.claim("worker-1", batch=5, visibility_timeout_seconds=3600)
    assert len(claimed) == 1
    assert claimed[0].status is JobStatus.RUNNING
    assert claimed[0].attempts == 1

    # Nothing else runnable: the running job is locked and fresh.
    assert store.claim("worker-2", batch=5, visibility_timeout_seconds=3600) == []


def test_mark_succeeded_is_terminal(control_plane_db: ControlPlaneDatabase) -> None:
    store = _store(control_plane_db)
    job_id = store.enqueue(tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST)
    store.claim("worker-1", visibility_timeout_seconds=3600)

    store.mark_succeeded(job_id)

    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.SUCCEEDED
    assert record.finished_at is not None


def test_mark_failed_retries_then_dead_letters(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    store = _store(control_plane_db)
    job_id = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, max_attempts=2
    )

    # Attempt 1 -> retry (requeued, immediately available with zero backoff).
    store.claim("worker-1", visibility_timeout_seconds=3600)
    status = store.mark_failed(job_id, "boom", backoff_base_seconds=0.0)
    assert status is JobStatus.QUEUED

    # Attempt 2 -> attempts hits max_attempts -> dead letter.
    reclaimed = store.claim("worker-1", visibility_timeout_seconds=3600)
    assert len(reclaimed) == 1
    assert reclaimed[0].attempts == 2
    status = store.mark_failed(job_id, "boom again", backoff_base_seconds=0.0)
    assert status is JobStatus.DEAD_LETTER

    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.DEAD_LETTER
    assert record.last_error == "boom again"


def test_requeue_resets_dead_letter_for_a_fresh_attempt(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    store = _store(control_plane_db)
    job_id = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, max_attempts=1
    )
    store.claim("worker-1", visibility_timeout_seconds=3600)
    store.mark_failed(job_id, "boom", backoff_base_seconds=0.0)
    assert store.get(job_id, _TENANT).status is JobStatus.DEAD_LETTER  # type: ignore[union-attr]

    assert store.requeue(job_id, max_attempts=5) is True

    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.QUEUED
    assert record.attempts == 0
    assert record.max_attempts == 5
    assert record.last_error is None
    assert record.finished_at is None

    # The requeued job is immediately claimable again.
    claimed = store.claim("worker-2", visibility_timeout_seconds=3600)
    assert len(claimed) == 1
    assert claimed[0].id == job_id


def test_requeue_unknown_job_returns_false(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    store = _store(control_plane_db)
    assert store.requeue("does-not-exist") is False


def test_stale_running_job_is_reclaimed(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    store = _store(control_plane_db)
    store.enqueue(tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST)
    store.claim("worker-1", visibility_timeout_seconds=3600)

    # A negative visibility window forces the fresh lock to look stale.
    reclaimed = store.claim("worker-2", visibility_timeout_seconds=-1)
    assert len(reclaimed) == 1
    assert reclaimed[0].attempts == 2


def test_heartbeat_refreshes_lock_and_blocks_reclaim(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    from datetime import UTC, datetime, timedelta

    from domain.control_plane import IngestionJob

    store = _store(control_plane_db)
    job_id = store.enqueue(tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST)
    store.claim("worker-1", visibility_timeout_seconds=3600)

    # Age the lock so it would otherwise be reclaimed as stale.
    with control_plane_db.session() as session:
        session.get(IngestionJob, job_id).locked_at = datetime.now(UTC) - timedelta(
            seconds=1000
        )

    # A live worker's heartbeat refreshes the lock to "now".
    assert store.heartbeat(job_id) is True

    # With the lock fresh, another worker no longer sees it as stale.
    reclaimed = store.claim("worker-2", visibility_timeout_seconds=300)
    assert reclaimed == []


def test_heartbeat_returns_false_for_terminal_job(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    store = _store(control_plane_db)
    job_id = store.enqueue(tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST)
    store.claim("worker-1", visibility_timeout_seconds=3600)
    store.mark_succeeded(job_id)

    assert store.heartbeat(job_id) is False


def test_release_returns_job_to_queue_without_spending_attempt(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    store = _store(control_plane_db)
    job_id = store.enqueue(tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST)
    claimed = store.claim("worker-1", visibility_timeout_seconds=3600)
    assert claimed[0].attempts == 1

    store.release(job_id)

    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.QUEUED
    assert record.attempts == 0  # interrupted attempt refunded
    # Immediately claimable again by any worker.
    reclaimed = store.claim("worker-2", visibility_timeout_seconds=3600)
    assert len(reclaimed) == 1
    assert reclaimed[0].id == job_id


def test_backoff_defers_retry(control_plane_db: ControlPlaneDatabase) -> None:
    store = _store(control_plane_db)
    job_id = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, max_attempts=3
    )
    store.claim("worker-1", visibility_timeout_seconds=3600)
    store.mark_failed(job_id, "boom", backoff_base_seconds=600.0)

    # Requeued but scheduled in the future, so not immediately claimable.
    assert store.claim("worker-1", visibility_timeout_seconds=3600) == []

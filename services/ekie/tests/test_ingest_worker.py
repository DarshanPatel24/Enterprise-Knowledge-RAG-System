"""Tests for the durable ingestion job worker (:class:`IngestionJobWorker`)."""

from __future__ import annotations

from types import SimpleNamespace

from config.settings import IngestionSettings
from domain.control_plane import ControlPlaneDatabase, JobKind, JobStatus
from domain.jobs import JobQueueStore, SourceStore
from domain.jobs.worker import IngestionJobWorker
from domain.orchestration import WorkflowStatus

_TENANT = "tenant-w"


class _FakeOrchestrator:
    def __init__(self, *, result: object = None, exc: Exception | None = None) -> None:
        self._result = result
        self._exc = exc
        self.calls: list[tuple[str, str, bytes]] = []

    def run(self, document_id: str, tenant_id: str, *, source_bytes: bytes, **_: object):
        self.calls.append((document_id, tenant_id, source_bytes))
        if self._exc is not None:
            raise self._exc
        return self._result


class _FakeDeletion:
    def __init__(self, *, exc: Exception | None = None) -> None:
        self._exc = exc
        self.calls: list[tuple[str, str, bool]] = []

    def delete_document(self, document_id: str, tenant_id: str, *, force: bool = False):
        self.calls.append((document_id, tenant_id, force))
        if self._exc is not None:
            raise self._exc
        return None


def _settings() -> IngestionSettings:
    return IngestionSettings(
        max_attempts=3,
        claim_batch_size=5,
        poll_interval_seconds=0.01,
        retry_backoff_base_seconds=0.0,
        retry_backoff_multiplier=2.0,
        retry_backoff_max_seconds=1.0,
        visibility_timeout_seconds=3600.0,
    )


def _worker(
    store: JobQueueStore,
    orchestrator: object,
    deletion: object,
    source_store: SourceStore,
) -> IngestionJobWorker:
    return IngestionJobWorker(
        job_queue=store,
        orchestrator=orchestrator,  # type: ignore[arg-type]
        deletion_service=deletion,  # type: ignore[arg-type]
        source_store=source_store,
        settings=_settings(),
    )


def _completed() -> SimpleNamespace:
    return SimpleNamespace(status=WorkflowStatus.COMPLETED, failure=None)


def _dead_letter() -> SimpleNamespace:
    return SimpleNamespace(
        status=WorkflowStatus.DEAD_LETTER,
        failure=SimpleNamespace(
            stage=SimpleNamespace(value="embed"),
            error_type="EmbeddingError",
            message="boom",
        ),
    )


def _document_deleted() -> SimpleNamespace:
    """A workflow that failed because the document row no longer exists.

    A ``not_found`` error exhausts the per-stage retries and ends as
    ``DEAD_LETTER``; the worker recognizes the error type and cancels instead.
    """
    return SimpleNamespace(
        status=WorkflowStatus.DEAD_LETTER,
        failure=SimpleNamespace(
            stage=SimpleNamespace(value="transform"),
            error_type="not_found",
            message="document 'doc-1' not found for tenant 'tenant-w'",
        ),
    )


def test_worker_completes_ingest_job(control_plane_db: ControlPlaneDatabase) -> None:
    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    sources.store(_TENANT, "doc-1", b"# hi")
    job_id = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, content_hash="h"
    )
    orchestrator = _FakeOrchestrator(result=_completed())

    handled = _worker(store, orchestrator, _FakeDeletion(), sources).process_once("w1")

    assert handled == 1
    assert orchestrator.calls[0] == ("doc-1", _TENANT, b"# hi")
    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.SUCCEEDED


def test_worker_retries_then_dead_letters_failed_ingest(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    sources.store(_TENANT, "doc-1", b"# hi")
    job_id = store.enqueue(
        tenant_id=_TENANT,
        document_id="doc-1",
        kind=JobKind.INGEST,
        content_hash="h",
        max_attempts=2,
    )
    worker = _worker(store, _FakeOrchestrator(result=_dead_letter()), _FakeDeletion(), sources)

    worker.process_once("w1")
    assert store.get(job_id, _TENANT).status is JobStatus.QUEUED  # type: ignore[union-attr]

    worker.process_once("w1")
    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.DEAD_LETTER
    assert "embed" in (record.last_error or "")


def test_worker_cancels_ingest_without_source_bytes(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    job_id = store.enqueue(
        tenant_id=_TENANT,
        document_id="doc-1",
        kind=JobKind.INGEST,
        content_hash="h",
        max_attempts=3,
    )
    orchestrator = _FakeOrchestrator(result=_completed())

    _worker(store, orchestrator, _FakeDeletion(), sources).process_once("w1")

    # A missing staged source is permanent (document deleted) -> cancel, do not
    # retry into dead letter; no operator cleanup required.
    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.CANCELLED
    assert "source" in (record.last_error or "")
    assert orchestrator.calls == []


def test_worker_cancels_ingest_when_document_deleted(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    sources.store(_TENANT, "doc-1", b"# hi")
    job_id = store.enqueue(
        tenant_id=_TENANT,
        document_id="doc-1",
        kind=JobKind.INGEST,
        content_hash="h",
        max_attempts=3,
    )
    worker = _worker(store, _FakeOrchestrator(result=_document_deleted()), _FakeDeletion(), sources)

    worker.process_once("w1")

    # not_found means the document was deleted mid-flight: cancel (terminal, no
    # retries), and clean up the staged source so nothing lingers.
    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.CANCELLED
    assert "no longer exists" in (record.last_error or "")
    assert sources.load(_TENANT, "doc-1") is None


def test_worker_heartbeats_long_running_job(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    import time as _time

    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    sources.store(_TENANT, "doc-1", b"# hi")
    job_id = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, content_hash="h"
    )

    calls = {"n": 0}
    original = store.heartbeat

    def _spy(jid: str) -> bool:
        calls["n"] += 1
        return original(jid)

    store.heartbeat = _spy  # type: ignore[method-assign]

    class _SlowOrchestrator:
        def run(self, *_: object, **__: object):
            _time.sleep(0.25)
            return _completed()

    settings = IngestionSettings(
        claim_batch_size=1,
        poll_interval_seconds=0.01,
        heartbeat_interval_seconds=0.05,
        visibility_timeout_seconds=3600.0,
    )
    worker = IngestionJobWorker(
        job_queue=store,
        orchestrator=_SlowOrchestrator(),  # type: ignore[arg-type]
        deletion_service=_FakeDeletion(),  # type: ignore[arg-type]
        source_store=sources,
        settings=settings,
    )

    worker.process_once("w1")

    # A job that outlives the heartbeat interval is pinged at least once so a
    # live worker's lock never ages into a stale reclaim.
    assert calls["n"] >= 1
    assert store.get(job_id, _TENANT).status is JobStatus.SUCCEEDED


def test_worker_processes_delete_job(control_plane_db: ControlPlaneDatabase) -> None:
    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    job_id = store.enqueue(
        tenant_id=_TENANT,
        document_id="doc-1",
        kind=JobKind.DELETE,
        force=True,
    )
    deletion = _FakeDeletion()

    _worker(store, _FakeOrchestrator(), deletion, sources).process_once("w1")

    assert deletion.calls == [("doc-1", _TENANT, True)]
    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.SUCCEEDED


def test_worker_marks_failed_on_exception(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    sources.store(_TENANT, "doc-1", b"# hi")
    job_id = store.enqueue(
        tenant_id=_TENANT,
        document_id="doc-1",
        kind=JobKind.INGEST,
        content_hash="h",
        max_attempts=1,
    )
    orchestrator = _FakeOrchestrator(exc=RuntimeError("kaboom"))

    _worker(store, orchestrator, _FakeDeletion(), sources).process_once("w1")

    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.DEAD_LETTER
    assert "kaboom" in (record.last_error or "")


def test_worker_releases_job_on_keyboard_interrupt(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    sources = SourceStore(control_plane_db)
    store = JobQueueStore(control_plane_db)
    sources.store(_TENANT, "doc-1", b"# hi")
    job_id = store.enqueue(
        tenant_id=_TENANT, document_id="doc-1", kind=JobKind.INGEST, content_hash="h"
    )
    orchestrator = _FakeOrchestrator(exc=KeyboardInterrupt())

    worker = _worker(store, orchestrator, _FakeDeletion(), sources)
    try:
        worker.process_once("w1")
    except KeyboardInterrupt:
        pass

    # The in-flight job is returned to the queue for a restarted worker.
    record = store.get(job_id, _TENANT)
    assert record is not None
    assert record.status is JobStatus.QUEUED
    assert record.attempts == 0

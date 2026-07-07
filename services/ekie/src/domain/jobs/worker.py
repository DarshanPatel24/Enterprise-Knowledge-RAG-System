"""Ingestion job worker: claims durable jobs and executes the pipeline.

A worker repeatedly claims runnable jobs from the :class:`JobQueueStore` and
executes them out of the HTTP request path. ``ingest`` jobs run the full
workflow orchestrator; ``delete`` jobs run the document deletion service. Each
job runs inside a correlation scope so logs and traces carry the originating
tenant and correlation identifiers. Successes are marked terminal; failures are
requeued with backoff until the attempt budget is exhausted (dead letter).
"""

from __future__ import annotations

import time
from contextlib import suppress
from threading import Event, Thread

from config.settings import IngestionSettings
from domain.control_plane import JobKind
from domain.jobs.queue import JobQueueStore, JobRecord
from domain.jobs.source import SourceStore
from domain.observability import correlation_scope
from domain.orchestration import WorkflowOrchestrator, WorkflowResult, WorkflowStatus
from domain.publishing import DocumentDeletionService


def _failure_reason(result: WorkflowResult) -> str:
    """Summarize why a workflow did not complete."""
    if result.failure is not None:
        failure = result.failure
        return f"{failure.stage.value}:{failure.error_type}: {failure.message}"
    return f"workflow ended with status {result.status.value}"


def _document_was_deleted(result: WorkflowResult) -> bool:
    """Return ``True`` when the workflow failed only because the document is gone.

    Every stage raises a ``not_found`` error when the document row no longer
    exists (it was deleted while the job waited in the queue). This is a benign,
    non-retryable condition: the job is moot and should be cancelled rather than
    retried into dead letter.
    """
    return result.failure is not None and result.failure.error_type == "not_found"


class IngestionJobWorker:
    """Executes durable ingestion jobs claimed from the queue."""

    def __init__(
        self,
        *,
        job_queue: JobQueueStore,
        orchestrator: WorkflowOrchestrator,
        deletion_service: DocumentDeletionService,
        source_store: SourceStore,
        settings: IngestionSettings,
    ) -> None:
        self._queue = job_queue
        self._orchestrator = orchestrator
        self._deletion = deletion_service
        self._source_store = source_store
        self._settings = settings

    def process_once(self, worker_id: str) -> int:
        """Claim and process one batch of jobs; return how many were handled."""
        claimed = self._queue.claim(
            worker_id,
            batch=self._settings.claim_batch_size,
            visibility_timeout_seconds=self._settings.visibility_timeout_seconds,
        )
        for record in claimed:
            try:
                self._process_with_heartbeat(record)
            except (KeyboardInterrupt, SystemExit):
                # Graceful shutdown mid-job: return the job to the queue so a
                # restarted worker resumes it immediately instead of waiting for
                # the visibility timeout to expire.
                self._queue.release(record.id)
                raise
        return len(claimed)

    def run_forever(self, worker_id: str, *, stop: Event | None = None) -> None:
        """Continuously process jobs until ``stop`` is set, sleeping when idle."""
        while stop is None or not stop.is_set():
            processed = self.process_once(worker_id)
            if processed == 0:
                time.sleep(self._settings.poll_interval_seconds)

    def _process_with_heartbeat(self, record: JobRecord) -> None:
        """Process a job while a background thread keeps its lock fresh.

        Long stages (embedding, intelligence) can outlast the visibility
        timeout. The heartbeat refreshes ``locked_at`` so a live worker's job is
        never mistaken for an orphan; if this worker dies the heartbeat stops and
        the lock ages out, letting a restarted worker reclaim and resume the job.
        """
        stop = Event()
        interval = max(0.05, self._settings.heartbeat_interval_seconds)

        def _beat() -> None:
            while not stop.wait(interval):
                # A heartbeat blip (transient DB error) must not kill the thread;
                # the next tick retries and the lock stays fresh in aggregate.
                with suppress(Exception):
                    self._queue.heartbeat(record.id)

        beater = Thread(target=_beat, name=f"hb-{record.id[:8]}", daemon=True)
        beater.start()
        try:
            self._process(record)
        finally:
            stop.set()
            beater.join(timeout=2.0)

    def _process(self, record: JobRecord) -> None:
        try:
            with correlation_scope(
                tenant_id=record.tenant_id,
                correlation_id=record.correlation_id or record.id,
            ):
                if record.kind is JobKind.INGEST:
                    self._process_ingest(record)
                elif record.kind is JobKind.DELETE:
                    self._process_delete(record)
                else:  # pragma: no cover - defensive
                    self._fail(record, f"unknown job kind: {record.kind}")
        except Exception as exc:  # noqa: BLE001 - isolate the worker from job failures
            self._fail(record, f"{type(exc).__name__}: {exc}")

    def _process_ingest(self, record: JobRecord) -> None:
        source = self._source_store.load(record.tenant_id, record.document_id)
        if source is None:
            # The staged source is stored durably before the job is enqueued, so
            # its absence is permanent -- typically the document was deleted and
            # its source cleaned up. Retrying cannot recover it, so cancel the
            # now-orphaned job instead of burning attempts into dead letter.
            self._cancel(
                record,
                "source bytes unavailable (document likely deleted); cancelling orphaned job",
            )
            return
        result = self._orchestrator.run(
            record.document_id,
            record.tenant_id,
            source_bytes=source,
            mime_type=record.mime_type,
            correlation_id=record.correlation_id,
            intelligence_provider=record.intelligence_provider,
            intelligence_model=record.intelligence_model,
            embedding_provider=record.embedding_provider,
            embedding_model=record.embedding_model,
        )
        if result.status is WorkflowStatus.COMPLETED:
            self._queue.mark_succeeded(record.id)
            self._source_store.delete(record.tenant_id, record.document_id)
        elif _document_was_deleted(result):
            self._cancel(
                record,
                "document no longer exists; cancelling orphaned ingest job",
            )
        else:
            self._fail(record, _failure_reason(result))

    def _process_delete(self, record: JobRecord) -> None:
        self._deletion.delete_document(
            record.document_id, record.tenant_id, force=record.force
        )
        self._queue.mark_succeeded(record.id)

    def _cancel(self, record: JobRecord, reason: str) -> None:
        """Terminally cancel an orphaned job and clean up its staged source."""
        self._queue.cancel(record.id, reason)
        self._source_store.delete(record.tenant_id, record.document_id)

    def _fail(self, record: JobRecord, reason: str) -> None:
        self._queue.mark_failed(
            record.id,
            reason,
            backoff_base_seconds=self._settings.retry_backoff_base_seconds,
            backoff_multiplier=self._settings.retry_backoff_multiplier,
            backoff_max_seconds=self._settings.retry_backoff_max_seconds,
        )

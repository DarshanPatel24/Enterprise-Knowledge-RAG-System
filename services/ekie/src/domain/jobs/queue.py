"""Durable ingestion job queue backed by the Control Plane database.

Implements an outbox-style work queue over the ``ingestion_jobs`` table. The API
enqueues jobs; a worker pool claims and executes them. Claiming uses an atomic
"select-and-lock" transaction — on Microsoft SQL Server it applies
``WITH (UPDLOCK, READPAST, ROWLOCK)`` so concurrent workers skip each other's
locked rows; on SQLite the hint is ignored and the single-writer transaction is
sufficient for local use. Stale locks (from crashed workers) are reclaimed once
older than the configured visibility timeout.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_

from domain.control_plane import (
    ControlPlaneDatabase,
    IngestionJob,
    JobKind,
    JobStatus,
)

_ACTIVE_STATUSES = (JobStatus.QUEUED, JobStatus.RUNNING)
_ERROR_TEXT_LIMIT = 4000


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class JobRecord:
    """Detached snapshot of an ingestion job for use outside a DB session."""

    id: str
    tenant_id: str
    document_id: str
    kind: JobKind
    status: JobStatus
    content_hash: str
    source_path: str | None
    attempts: int
    max_attempts: int
    correlation_id: str | None
    mime_type: str | None
    intelligence_provider: str | None
    intelligence_model: str | None
    embedding_provider: str | None
    embedding_model: str | None
    force: bool
    last_error: str | None
    available_at: datetime
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


def _to_record(job: IngestionJob) -> JobRecord:
    return JobRecord(
        id=job.id,
        tenant_id=job.tenant_id,
        document_id=job.document_id,
        kind=JobKind(job.kind),
        status=JobStatus(job.status),
        content_hash=job.content_hash,
        source_path=job.source_path,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        correlation_id=job.correlation_id,
        mime_type=job.mime_type,
        intelligence_provider=job.intelligence_provider,
        intelligence_model=job.intelligence_model,
        embedding_provider=job.embedding_provider,
        embedding_model=job.embedding_model,
        force=job.force,
        last_error=job.last_error,
        available_at=job.available_at,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


class JobQueueStore:
    """Durable, tenant-scoped work queue over the ``ingestion_jobs`` table."""

    def __init__(self, db: ControlPlaneDatabase) -> None:
        self._db = db

    def enqueue(
        self,
        *,
        tenant_id: str,
        document_id: str,
        kind: JobKind,
        content_hash: str = "",
        source_path: str | None = None,
        max_attempts: int = 3,
        priority: int = 0,
        correlation_id: str | None = None,
        mime_type: str | None = None,
        intelligence_provider: str | None = None,
        intelligence_model: str | None = None,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
        force: bool = False,
        dedupe: bool = True,
    ) -> str:
        """Insert a job and return its id.

        When ``dedupe`` is true an existing non-terminal job for the same
        ``(tenant_id, document_id, kind, content_hash)`` is reused instead of
        creating a duplicate, making repeated submissions idempotent.
        """
        with self._db.session() as session:
            if dedupe:
                existing = (
                    session.query(IngestionJob)
                    .filter(
                        IngestionJob.tenant_id == tenant_id,
                        IngestionJob.document_id == document_id,
                        IngestionJob.kind == kind,
                        IngestionJob.content_hash == content_hash,
                        IngestionJob.status.in_(_ACTIVE_STATUSES),
                    )
                    .first()
                )
                if existing is not None:
                    return existing.id

            job = IngestionJob(
                tenant_id=tenant_id,
                document_id=document_id,
                kind=kind,
                status=JobStatus.QUEUED,
                content_hash=content_hash,
                source_path=source_path,
                priority=priority,
                max_attempts=max_attempts,
                available_at=_utc_now(),
                correlation_id=correlation_id,
                mime_type=mime_type,
                intelligence_provider=intelligence_provider,
                intelligence_model=intelligence_model,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
                force=force,
            )
            session.add(job)
            session.flush()
            return job.id

    def claim(
        self,
        worker_id: str,
        *,
        batch: int = 1,
        visibility_timeout_seconds: float = 3600.0,
    ) -> list[JobRecord]:
        """Atomically claim up to ``batch`` runnable jobs for ``worker_id``.

        A job is runnable when it is due (``available_at`` reached) and either
        queued or a stale-running job whose lock exceeded the visibility timeout.
        Claiming transitions the job to running, records the lock, and increments
        the attempt counter.
        """
        now = _utc_now()
        stale_before = now - timedelta(seconds=visibility_timeout_seconds)
        with self._db.session() as session:
            query = (
                session.query(IngestionJob)
                .filter(
                    IngestionJob.available_at <= now,
                    or_(
                        IngestionJob.status == JobStatus.QUEUED,
                        and_(
                            IngestionJob.status == JobStatus.RUNNING,
                            IngestionJob.locked_at < stale_before,
                        ),
                    ),
                )
                .order_by(
                    IngestionJob.priority.desc(),
                    IngestionJob.available_at.asc(),
                    IngestionJob.created_at.asc(),
                )
                .with_hint(IngestionJob, "WITH (UPDLOCK, READPAST, ROWLOCK)", "mssql")
                .limit(batch)
            )
            claimed: list[JobRecord] = []
            for job in query.all():
                job.status = JobStatus.RUNNING
                job.locked_by = worker_id
                job.locked_at = now
                job.attempts += 1
                if job.started_at is None:
                    job.started_at = now
                claimed.append(_to_record(job))
            return claimed

    def mark_succeeded(self, job_id: str) -> None:
        """Mark a job as successfully completed and release its lock."""
        with self._db.session() as session:
            job = session.get(IngestionJob, job_id)
            if job is None:
                return
            job.status = JobStatus.SUCCEEDED
            job.finished_at = _utc_now()
            job.locked_by = None
            job.locked_at = None
            job.last_error = None

    def release(self, job_id: str) -> None:
        """Return a running job to the queue for prompt re-claim (e.g. on shutdown).

        The interrupted attempt is not counted against the retry budget so a
        graceful restart resumes the job without eroding its remaining attempts.
        """
        with self._db.session() as session:
            job = session.get(IngestionJob, job_id)
            if job is None or job.status != JobStatus.RUNNING:
                return
            job.status = JobStatus.QUEUED
            job.locked_by = None
            job.locked_at = None
            job.available_at = _utc_now()
            if job.attempts > 0:
                job.attempts -= 1

    def heartbeat(self, job_id: str) -> bool:
        """Refresh a running job's lock so a live worker is not seen as stale.

        Long-running stages can exceed the visibility timeout. A worker calls
        this periodically while a job executes; the fresh ``locked_at`` prevents
        other workers from reclaiming a job that is still being processed. A
        crashed worker stops heartbeating, so its lock ages out and the job is
        reclaimed and resumed promptly. Returns ``True`` while the job is running.
        """
        with self._db.session() as session:
            job = session.get(IngestionJob, job_id)
            if job is None or job.status != JobStatus.RUNNING:
                return False
            job.locked_at = _utc_now()
            return True

    def cancel(self, job_id: str, reason: str) -> bool:
        """Terminally cancel a job that can never succeed.

        Used when a job's target document no longer exists (it was deleted).
        Unlike a failure, a cancellation does not consume retries or move to
        dead letter -- it is a benign terminal state needing no operator action.
        Returns ``True`` when a job was cancelled.
        """
        with self._db.session() as session:
            job = session.get(IngestionJob, job_id)
            if job is None:
                return False
            job.status = JobStatus.CANCELLED
            job.finished_at = _utc_now()
            job.locked_by = None
            job.locked_at = None
            job.last_error = (reason or "")[:_ERROR_TEXT_LIMIT]
            return True

    def requeue(self, job_id: str, *, max_attempts: int | None = None) -> bool:
        """Reset a terminal or stuck job back to ``QUEUED`` for a fresh attempt.

        Intended for operator-driven recovery of dead-lettered (or failed) jobs
        after the underlying cause has been fixed. Because the orchestrator is
        resumable (it reconciles completed stages from asset rows), a requeued
        job continues from the first incomplete stage rather than restarting.
        The attempt counter is reset and the retry budget may be widened via
        ``max_attempts``. Returns ``True`` when a job was reset.
        """
        with self._db.session() as session:
            job = session.get(IngestionJob, job_id)
            if job is None:
                return False
            job.status = JobStatus.QUEUED
            job.attempts = 0
            if max_attempts is not None:
                job.max_attempts = max_attempts
            job.locked_by = None
            job.locked_at = None
            job.available_at = _utc_now()
            job.started_at = None
            job.finished_at = None
            job.last_error = None
            return True

    def mark_failed(
        self,
        job_id: str,
        error: str,
        *,
        backoff_base_seconds: float = 30.0,
        backoff_multiplier: float = 2.0,
        backoff_max_seconds: float = 900.0,
    ) -> JobStatus:
        """Record a failure, then requeue with backoff or move to dead letter.

        Returns the resulting status (``QUEUED`` when it will retry,
        ``DEAD_LETTER`` when the attempt budget is exhausted).
        """
        now = _utc_now()
        with self._db.session() as session:
            job = session.get(IngestionJob, job_id)
            if job is None:
                return JobStatus.DEAD_LETTER
            job.last_error = (error or "")[:_ERROR_TEXT_LIMIT]
            job.locked_by = None
            job.locked_at = None
            if job.attempts >= job.max_attempts:
                job.status = JobStatus.DEAD_LETTER
                job.finished_at = now
                return JobStatus.DEAD_LETTER
            delay = min(
                backoff_base_seconds * (backoff_multiplier ** max(job.attempts - 1, 0)),
                backoff_max_seconds,
            )
            job.status = JobStatus.QUEUED
            job.available_at = now + timedelta(seconds=delay)
            return JobStatus.QUEUED

    def get(self, job_id: str, tenant_id: str) -> JobRecord | None:
        """Return a tenant-scoped job snapshot, or ``None`` if absent."""
        with self._db.session() as session:
            job = session.get(IngestionJob, job_id)
            if job is None or job.tenant_id != tenant_id:
                return None
            return _to_record(job)

    def latest_for_document(
        self, document_id: str, tenant_id: str
    ) -> JobRecord | None:
        """Return the most recent job for a document, or ``None``."""
        with self._db.session() as session:
            job = (
                session.query(IngestionJob)
                .filter(
                    IngestionJob.tenant_id == tenant_id,
                    IngestionJob.document_id == document_id,
                )
                .order_by(IngestionJob.created_at.desc())
                .first()
            )
            return None if job is None else _to_record(job)

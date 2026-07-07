"""Maintenance tool to inspect and requeue dead-lettered ingestion jobs.

A job that exhausts its retry budget moves to ``dead_letter`` and stops. After
the underlying cause is fixed (for example a vector-collection dimension
conflict), use this tool to reset the job back to ``queued`` so an ingestion
worker re-claims it. Because the orchestrator is resumable -- it reconciles
already-completed stages from the ``assets`` table -- a requeued job continues
from the first incomplete stage (typically Publish) rather than restarting the
whole pipeline.

Usage (from any directory):
    # Inspect failed / dead-lettered jobs
    python services/ekie/scripts/requeue_jobs.py --list

    # Requeue a single job (by job id or by document id)
    python services/ekie/scripts/requeue_jobs.py --job-id <id>
    python services/ekie/scripts/requeue_jobs.py --document-id <id>

    # Requeue every dead-lettered job for the tenant
    python services/ekie/scripts/requeue_jobs.py --all-dead

Add --max-attempts to widen the retry budget on requeue, --yes to skip the
confirmation prompt, and --tenant-id to override the configured tenant.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.chdir(_SERVICE_ROOT)

from config.settings import get_settings  # noqa: E402 - follows sys.path bootstrap
from domain.control_plane import ControlPlaneDatabase  # noqa: E402
from domain.control_plane.models import IngestionJob, JobStatus  # noqa: E402
from domain.jobs.queue import JobQueueStore  # noqa: E402

_RECOVERABLE = (JobStatus.DEAD_LETTER, JobStatus.FAILED)


def _resolve_tenant(explicit: str | None) -> str:
    if explicit:
        return explicit
    return get_settings().sync.tenant_id


def _select_targets(
    db: ControlPlaneDatabase,
    tenant_id: str,
    *,
    job_id: str | None,
    document_id: str | None,
    all_dead: bool,
) -> list[tuple[str, str, str, int]]:
    """Return (job_id, document_id, status, attempts) tuples to requeue."""
    with db.session() as session:
        query = session.query(IngestionJob).filter(
            IngestionJob.tenant_id == tenant_id
        )
        if job_id:
            query = query.filter(IngestionJob.id == job_id)
        elif document_id:
            query = query.filter(IngestionJob.document_id == document_id)
        else:
            query = query.filter(IngestionJob.status.in_(_RECOVERABLE))
        query = query.order_by(IngestionJob.created_at.desc())
        return [
            (j.id, j.document_id, str(j.status), j.attempts) for j in query.all()
        ]


def _list_jobs(db: ControlPlaneDatabase, tenant_id: str) -> int:
    with db.session() as session:
        jobs = (
            session.query(IngestionJob)
            .filter(
                IngestionJob.tenant_id == tenant_id,
                IngestionJob.status.in_(_RECOVERABLE),
            )
            .order_by(IngestionJob.created_at.desc())
            .all()
        )
        if not jobs:
            print("No failed or dead-lettered jobs for tenant", tenant_id)
            return 0
        print(f"Recoverable jobs for tenant {tenant_id!r}:\n")
        for j in jobs:
            print(
                f"  {j.id}  kind={j.kind}  status={j.status}  "
                f"attempts={j.attempts}/{j.max_attempts}  doc={j.document_id}"
            )
            print(f"      error: {(j.last_error or '')[:200]}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect and requeue dead-lettered ingestion jobs"
    )
    parser.add_argument("--tenant-id", default=None)
    parser.add_argument("--list", action="store_true", dest="do_list")
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--document-id", default=None)
    parser.add_argument("--all-dead", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=None)
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    db = ControlPlaneDatabase(get_settings().control_plane)
    db.run_migrations()
    tenant_id = _resolve_tenant(args.tenant_id)

    if args.do_list or not (args.job_id or args.document_id or args.all_dead):
        return _list_jobs(db, tenant_id)

    targets = _select_targets(
        db,
        tenant_id,
        job_id=args.job_id,
        document_id=args.document_id,
        all_dead=args.all_dead,
    )
    if not targets:
        print("No matching jobs to requeue.")
        return 0

    print(f"About to requeue {len(targets)} job(s):")
    for jid, doc, status, attempts in targets:
        print(f"  {jid}  status={status}  attempts={attempts}  doc={doc}")
    if not args.yes:
        reply = input("Proceed? [y/N] ").strip().lower()
        if reply not in {"y", "yes"}:
            print("Aborted.")
            return 1

    store = JobQueueStore(db)
    reset = 0
    for jid, _doc, _status, _attempts in targets:
        if store.requeue(jid, max_attempts=args.max_attempts):
            reset += 1
    print(f"Requeued {reset} job(s). Start an ingestion worker to process them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

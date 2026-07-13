"""Durable ingestion job worker process.

Claims and executes queued ingestion and deletion jobs from the Control Plane
job queue, decoupled from the HTTP request path. Run one or more of these
alongside the API so that enabling ``EKIE_INGESTION__ASYNC_ENABLED=true`` has
workers to execute the enqueued jobs.

Usage (from any directory):
    python services/ekie/scripts/production_ingest_worker.py
    python services/ekie/scripts/production_ingest_worker.py --worker-id w1
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.chdir(_SERVICE_ROOT)

from composition import (  # noqa: E402 - follows sys.path bootstrap
    build_asset_storage,
    build_workflow_orchestrator,
)
from config.settings import get_settings  # noqa: E402
from domain.control_plane import ControlPlaneDatabase  # noqa: E402
from domain.jobs import JobQueueStore, SourceStore  # noqa: E402
from domain.jobs.worker import IngestionJobWorker  # noqa: E402
from domain.publishing import (  # noqa: E402
    DocumentDeletionService,
    VectorCleanupService,
    cleanup_provider_registry,
)


def run_ingest_worker(worker_id: str) -> None:
    settings = get_settings()
    db = ControlPlaneDatabase(settings.control_plane)
    db.create_all()
    db.run_migrations()

    storage = build_asset_storage(settings)
    orchestrator = build_workflow_orchestrator(settings, db, storage)
    qdrant = settings.qdrant
    deletion_service = DocumentDeletionService(
        db,
        VectorCleanupService(
            db,
            storage,
            cleanup_provider_registry(
                qdrant_host=qdrant.host,
                qdrant_port=qdrant.port,
                qdrant_timeout_seconds=qdrant.request_timeout_seconds,
            ),
            fallback_provider=settings.publishing.provider,
            fallback_collection=settings.publishing.default_collection,
        ),
    )
    worker = IngestionJobWorker(
        job_queue=JobQueueStore(db),
        orchestrator=orchestrator,
        deletion_service=deletion_service,
        source_store=SourceStore(db),
        settings=settings.ingestion,
    )

    print("==================================================")
    print(" EKIE Ingestion Job Worker Started")
    print("==================================================")
    print(f" Worker ID        : {worker_id}")
    print(f" Poll Interval    : {settings.ingestion.poll_interval_seconds} seconds")
    print(f" Claim Batch Size : {settings.ingestion.claim_batch_size}")
    print(f" Max Attempts     : {settings.ingestion.max_attempts}")
    print("==================================================\n", flush=True)

    # Eagerly load the embedding model now so the (multi-GB, often GPU) weights
    # are resident before the first job is claimed. This surfaces any model-load
    # failure at startup instead of intermittently mid-ingestion, and removes the
    # first-document latency spike caused by lazy loading.
    print(
        f" Embedding provider : {settings.embedding.provider} "
        f"({settings.embedding.default_model or 'default'})"
    )
    print(" Loading embedding model (eager warm-up)...", flush=True)
    try:
        orchestrator.warm_up()
        print(" Embedding model loaded. Ready to process jobs.\n", flush=True)
    except Exception as exc:  # noqa: BLE001 - report and continue; lazy load will retry
        print(
            f" [warn] Eager model warm-up failed ({exc}); the model will load "
            "lazily on the first job.\n",
            flush=True,
        )

    try:
        worker.run_forever(worker_id)
    except KeyboardInterrupt:
        print("\n[worker] Stopped.")


def main() -> int:
    parser = argparse.ArgumentParser(description="EKIE durable ingestion job worker")
    parser.add_argument(
        "--worker-id",
        default=f"{socket.gethostname()}-{os.getpid()}",
        help="Unique identifier for this worker (defaults to host-pid)",
    )
    args = parser.parse_args()
    run_ingest_worker(args.worker_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""One-off recovery: reset dead-lettered docs whose stage payloads were lost.

Before persistent local asset storage existed, stage payloads lived only in the
worker's memory, so a restart could leave a document with asset *rows* but no
readable payload -- resumes then failed with "payload unavailable". This clears
such a document's stage assets, processing state, and workflow rows (keeping the
document and its DB-stored source) and requeues its ingest job so it re-runs
cleanly from source into the now-persistent storage.

Run only after restarting the API and worker so they use the persistent store.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
os.chdir(_SERVICE_ROOT)

from config.settings import get_settings  # noqa: E402
from domain.control_plane import ControlPlaneDatabase  # noqa: E402
from domain.control_plane.models import (  # noqa: E402
    Asset,
    IngestionJob,
    JobKind,
    JobStatus,
    ProcessingState,
    Workflow,
)
from domain.jobs import JobQueueStore, SourceStore  # noqa: E402

_PAYLOAD_ERRORS = ("payload unavailable", "missing_markdown", "missing_chunks")


def main() -> int:
    settings = get_settings()
    tenant_id = settings.sync.tenant_id
    db = ControlPlaneDatabase(settings.control_plane)
    db.run_migrations()
    sources = SourceStore(db)
    queue = JobQueueStore(db)

    with db.session() as sess:
        dead = (
            sess.query(IngestionJob)
            .filter(
                IngestionJob.tenant_id == tenant_id,
                IngestionJob.kind == JobKind.INGEST,
                IngestionJob.status == JobStatus.DEAD_LETTER,
            )
            .all()
        )
        targets = [
            (j.id, j.document_id)
            for j in dead
            if any(tok in (j.last_error or "") for tok in _PAYLOAD_ERRORS)
        ]

    if not targets:
        print("No dead-lettered documents with lost payloads to recover.")
        return 0

    recovered = 0
    for job_id, document_id in targets:
        if sources.load(tenant_id, document_id) is None:
            print(f"  SKIP {document_id}: no stored source; re-add it from the source folder.")
            continue
        with db.session() as sess:
            for asset in sess.query(Asset).filter(Asset.document_id == document_id).all():
                sess.delete(asset)  # cascades lineage rows
            sess.query(ProcessingState).filter(
                ProcessingState.document_id == document_id
            ).delete()
            sess.query(Workflow).filter(Workflow.document_id == document_id).delete()
        queue.requeue(job_id)
        recovered += 1
        print(f"  RESET {document_id}: cleared stage assets/state and requeued.")

    print(
        f"\nRecovered {recovered} document(s). Ensure the API and worker are running "
        "with persistent storage; the worker will re-ingest them from source."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

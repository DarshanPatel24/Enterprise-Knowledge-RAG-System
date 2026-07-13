"""Report per-document ingestion status from the Control Plane.

Lists every document EKIE knows about with its latest ingestion job status,
attempts, last error, and which pipeline stages (markdown/intelligence/chunks/
embedding/vector) completed. Use it to see why a document never reached the
vector store (failed job, stuck stage, or never queued).

Usage (from any directory):
    services/ekie/.venv/Scripts/python.exe services/ekie/scripts/ingestion_status.py
    ... ingestion_status.py --tenant-id tenant-default --unfinished-only
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

from config.settings import get_settings  # noqa: E402
from domain.control_plane import ControlPlaneDatabase  # noqa: E402

_STAGES = ("markdown", "intelligence", "chunks", "embedding", "vector")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tenant-id",
        default=None,
        help="Tenant to report on (default: EKIE_SYNC__TENANT_ID or all).",
    )
    parser.add_argument(
        "--unfinished-only",
        action="store_true",
        help="Only show documents that have not completed the vector stage.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    settings = get_settings()
    tenant_id = args.tenant_id or os.environ.get("EKIE_SYNC__TENANT_ID")

    db = ControlPlaneDatabase(settings.control_plane)
    from domain.control_plane.models import Asset, Document, IngestionJob

    with db.session() as sess:
        docs_query = sess.query(Document)
        if tenant_id:
            docs_query = docs_query.filter(Document.tenant_id == tenant_id)
        docs = docs_query.order_by(Document.source_path.asc()).all()
        doc_ids = [d.id for d in docs]

        assets = (
            sess.query(Asset).filter(Asset.document_id.in_(doc_ids)).all() if doc_ids else []
        )
        stages_by_doc: dict[str, set[str]] = {}
        for asset in assets:
            stages_by_doc.setdefault(asset.document_id, set()).add(str(asset.asset_type))

        jobs = (
            sess.query(IngestionJob)
            .filter(IngestionJob.document_id.in_(doc_ids))
            .order_by(IngestionJob.created_at.asc())
            .all()
            if doc_ids
            else []
        )
        job_by_doc: dict[str, IngestionJob] = {}
        for job in jobs:
            job_by_doc[job.document_id] = job  # keep the latest by created_at

        total = len(docs)
        published = 0
        rows: list[tuple[str, str, str]] = []
        for doc in docs:
            stages = stages_by_doc.get(doc.id, set())
            done = "vector" in stages
            if done:
                published += 1
            if args.unfinished_only and done:
                continue
            job = job_by_doc.get(doc.id)
            status = str(job.status) if job else "no-job"
            attempts = job.attempts if job else 0
            stage_marks = "".join(
                s[0].upper() if s in stages else "." for s in _STAGES
            )
            headline = f"{stage_marks}  {status:<12} a{attempts}  {doc.source_path}"
            error = (job.last_error if job and job.last_error else "").strip()
            rows.append((headline, error, doc.id))

    print(f"Tenant   : {tenant_id or '(all)'}")
    print(f"Documents: {total}   Published to vector store: {published}   Missing: {total - published}")
    print(f"Stages   : {'/'.join(_STAGES)}  (letter = done, . = pending)")
    print("=" * 90)
    for headline, error, doc_id in rows:
        print(headline)
        print(f"        id={doc_id}")
        if error:
            snippet = error.replace("\n", " ")[:400]
            print(f"        last_error: {snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

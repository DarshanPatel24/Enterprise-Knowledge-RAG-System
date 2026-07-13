"""Repair documents that the Control Plane marks published but Qdrant lacks.

When the Qdrant collection is wiped or partially lost without resetting the
Control Plane, EKIE still holds each document's ``vector`` asset record, and the
publish stage's dedup (``_existing_asset``) then skips re-publishing -- so the
points never return to Qdrant even though the embeddings still exist in asset
storage.

This repair reuses the already-computed embedding assets: for every document
missing from Qdrant it deletes the stale ``vector`` asset row (so dedup no longer
skips) and calls the publishing engine, which reads the stored embedding vectors
and pushes them straight into Qdrant. No re-embedding, no source bytes, and the
documents already present in Qdrant are never touched.

Dry-run by default; pass ``--apply`` to perform the repair. Qdrant and the
Control Plane database must be reachable (the API/workers need not be running).

Usage (from any directory):
    services/ekie/.venv/Scripts/python.exe services/ekie/scripts/repair_missing_qdrant_publish.py
    ... repair_missing_qdrant_publish.py --apply
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

from sqlalchemy import or_  # noqa: E402

from composition import build_asset_storage, build_publishing_engine  # noqa: E402
from config.settings import get_settings  # noqa: E402
from domain.control_plane import ControlPlaneDatabase  # noqa: E402
from domain.control_plane.models import Asset, AssetType, Document, Lineage  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete stale vector assets and re-publish (default: dry-run).",
    )
    parser.add_argument(
        "--rebuild-all",
        action="store_true",
        help=(
            "Recreate (empty) the collection and re-publish EVERY document from "
            "stored embeddings. Use after fixing the vector-identity scheme so "
            "previously collided points are rewritten with unique ids."
        ),
    )
    return parser.parse_args()


def _recreate_collection(settings: object) -> None:
    """Drop and recreate the collection with its existing vector params (empties it)."""
    from qdrant_client import QdrantClient
    from qdrant_client import models as qmodels

    qdrant = settings.qdrant  # type: ignore[attr-defined]
    collection = settings.publishing.default_collection  # type: ignore[attr-defined]
    client = QdrantClient(host=qdrant.host, port=qdrant.port)
    info = client.get_collection(collection)
    params = info.config.params.vectors
    size = params.size  # type: ignore[union-attr]
    distance = params.distance  # type: ignore[union-attr]
    client.delete_collection(collection)
    client.create_collection(
        collection,
        vectors_config=qmodels.VectorParams(size=size, distance=distance),
    )
    print(f"Recreated empty collection '{collection}' (dim={size}, distance={distance}).")


def _qdrant_present_paths(settings: object) -> set[str]:
    """Return the source paths that physically exist in Qdrant."""
    from qdrant_client import QdrantClient

    qdrant = settings.qdrant  # type: ignore[attr-defined]
    collection = settings.publishing.default_collection  # type: ignore[attr-defined]
    metadata_key = os.environ.get("EKRE_QDRANT__PAYLOAD_METADATA_KEY", "metadata")
    client = QdrantClient(host=qdrant.host, port=qdrant.port)
    present: set[str] = set()
    offset: object | None = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            meta = payload.get(metadata_key) if metadata_key else payload
            if not isinstance(meta, dict):
                meta = payload
            source_path = meta.get("source_path")
            if isinstance(source_path, str) and source_path:
                present.add(source_path)
        if offset is None:
            break
    return present


def _delete_vector_asset(db: ControlPlaneDatabase, document_id: str) -> int:
    """Delete a document's vector-stage asset rows and their lineage edges."""
    with db.session() as session:
        vector_ids = [
            row[0]
            for row in session.query(Asset.id).filter(
                Asset.document_id == document_id,
                Asset.asset_type == AssetType.VECTOR,
            )
        ]
        if not vector_ids:
            return 0
        session.query(Lineage).filter(
            or_(
                Lineage.asset_id.in_(vector_ids),
                Lineage.parent_asset_id.in_(vector_ids),
            )
        ).delete(synchronize_session=False)
        session.query(Asset).filter(Asset.id.in_(vector_ids)).delete(
            synchronize_session=False
        )
        return len(vector_ids)


def main() -> int:
    args = _parse_args()
    settings = get_settings()
    tenant_id = settings.sync.tenant_id
    db = ControlPlaneDatabase(settings.control_plane)
    db.run_migrations()
    storage = build_asset_storage(settings)
    engine = build_publishing_engine(settings, db, storage)

    present_paths = _qdrant_present_paths(settings)
    with db.session() as sess:
        docs = (
            sess.query(Document)
            .filter(Document.tenant_id == tenant_id)
            .order_by(Document.source_path.asc())
            .all()
        )
        doc_rows = [(d.id, d.source_path) for d in docs]

    if args.rebuild_all:
        targets = doc_rows
    else:
        targets = [row for row in doc_rows if row[1] not in present_paths]

    print(f"Tenant              : {tenant_id}")
    print(f"Documents in DB     : {len(docs)}")
    print(f"Present in Qdrant   : {len(present_paths)}")
    print(f"Targeted for repair : {len(targets)}")
    print(f"Mode                : {'REBUILD-ALL' if args.rebuild_all else 'repair-missing'}"
          f" / {'APPLY' if args.apply else 'DRY-RUN (no changes)'}")
    print("=" * 80)
    if not targets:
        print("Nothing to do.")
        return 0

    if args.apply and args.rebuild_all:
        _recreate_collection(settings)

    repaired = 0
    failed = 0
    for document_id, source_path in targets:
        if not args.apply:
            print(f"  WOULD re-publish {source_path}")
            continue
        try:
            _delete_vector_asset(db, document_id)
            result = engine.publish(document_id, tenant_id)
            print(f"  REPUBLISHED {source_path}  ({result.vector_count} vectors)")
            repaired += 1
        except Exception as exc:  # noqa: BLE001 - report and continue with the rest
            failed += 1
            print(
                f"  FAILED      {source_path}: {type(exc).__name__}: {exc}\n"
                "              (embedding payload likely missing; needs a full "
                "re-ingest from source)"
            )

    print("=" * 80)
    if args.apply:
        remaining = len(_qdrant_present_paths(settings))
        print(f"Repaired {repaired} document(s); {failed} failed.")
        print(f"Distinct documents now present in Qdrant: {remaining}")
    else:
        print(
            f"Dry-run: {len(targets)} document(s) would be re-published. "
            "Re-run with --apply to repair."
        )
    return 1 if args.apply and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

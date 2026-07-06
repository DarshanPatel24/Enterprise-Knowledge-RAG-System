"""Validate live Qdrant delete propagation through VectorCleanupService.

This script uses a real Qdrant instance, creates test vectors, stores a
published-vector payload, executes cleanup, and verifies vectors were removed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.settings import ControlPlaneSettings  # noqa: E402 - follows sys.path bootstrap
from domain.control_plane import (  # noqa: E402
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    Repository,
)
from domain.publishing import (  # noqa: E402
    PublishedVectorSet,
    SyncState,
    VectorCleanupService,
    VectorMetadata,
    VectorPoint,
    VectorRecord,
    cleanup_provider_registry,
)
from domain.publishing.collections import CollectionSpec  # noqa: E402
from domain.storage import InMemoryAssetStorage  # noqa: E402


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qdrant-host", default="localhost")
    parser.add_argument("--qdrant-port", type=int, default=6333)
    parser.add_argument("--qdrant-timeout", type=float, default=30.0)
    parser.add_argument("--collection", default="ekie_delete_validation")
    parser.add_argument("--output-dir", default="storage")
    args = parser.parse_args()

    tenant_id = "tenant-delete-validation"
    repository_id = "repo-delete-validation"
    document_id = "doc-delete-validation"

    db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
    db.create_all()
    storage = InMemoryAssetStorage()
    providers = cleanup_provider_registry(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        qdrant_timeout_seconds=args.qdrant_timeout,
    )
    provider = providers.get("qdrant")

    provider.ensure_collection(
        CollectionSpec(name=args.collection, dimension=4, distance_metric="cosine")
    )

    with db.session() as session:
        session.add(
            Repository(
                id=repository_id,
                tenant_id=tenant_id,
                name="delete-validation",
                source_type="local_fs",
                uri="D:/validation",
            )
        )
        session.add(
            Document(
                id=document_id,
                repository_id=repository_id,
                tenant_id=tenant_id,
                source_path="to-delete.md",
                content_hash="hash-1",
                classification_clearance="internal",
                version=1,
            )
        )
        session.add(
            Asset(
                document_id=document_id,
                tenant_id=tenant_id,
                asset_type=AssetType.VECTOR,
                version=1,
                storage_uri=f"asset://{tenant_id}/{document_id}/vectors?version=1",
                content_hash="payload-hash",
            )
        )

    vector_ids = [
        f"{args.collection}::chunk-1::e1",
        f"{args.collection}::chunk-2::e1",
    ]
    for index, vector_id in enumerate(vector_ids, start=1):
        provider.upsert(
            args.collection,
            [
                VectorPoint(
                    vector_id=vector_id,
                    values=[0.1 * index, 0.2 * index, 0.3 * index, 0.4 * index],
                    metadata=VectorMetadata(
                        document_id=document_id,
                        chunk_id=f"chunk-{index}",
                        tenant_id=tenant_id,
                        classification_clearance="internal",
                        distance_metric="cosine",
                        collection=args.collection,
                        embedding_model="validation-model",
                        embedding_version=1,
                        dimension=4,
                    ),
                )
            ],
        )

    published = PublishedVectorSet(
        document_id=document_id,
        collection=args.collection,
        provider="qdrant",
        model_name="validation-model",
        distance_metric="cosine",
        dimension=4,
        vector_count=2,
        source_embedding_version=1,
        records=[
            VectorRecord(
                vector_id=vector_ids[0],
                chunk_id="chunk-1",
                chunk_content_hash="c1",
                state=SyncState.PUBLISHED,
            ),
            VectorRecord(
                vector_id=vector_ids[1],
                chunk_id="chunk-2",
                chunk_content_hash="c2",
                state=SyncState.PUBLISHED,
            ),
        ],
    )
    storage.put(f"{tenant_id}/{document_id}/vectors", published.canonical_json(), version=1)

    before_fetch = [provider.fetch(args.collection, vector_id) for vector_id in vector_ids]

    cleaner = VectorCleanupService(db, storage, providers)
    cleanup_result = cleaner.purge_document_vectors(document_id, tenant_id)

    after_fetch = [provider.fetch(args.collection, vector_id) for vector_id in vector_ids]

    result = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "qdrant_host": args.qdrant_host,
        "qdrant_port": args.qdrant_port,
        "collection": args.collection,
        "document_id": document_id,
        "before_present": [entry is not None for entry in before_fetch],
        "after_present": [entry is not None for entry in after_fetch],
        "cleanup_deleted_count": cleanup_result.deleted_count if cleanup_result else 0,
        "accepted": bool(cleanup_result) and cleanup_result.deleted_count == 2 and all(
            entry is None for entry in after_fetch
        ),
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"qdrant_delete_validation_{_timestamp()}.json"
    output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(f"RESULT_FILE={output_file}")
    return 0 if result["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

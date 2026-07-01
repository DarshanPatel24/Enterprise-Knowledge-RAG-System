"""Manual demo for the EKIE Embedding Framework (EKIE-S5).

Runs the full local pipeline over a temp file: synchronize (S1) -> transform to
canonical Markdown (S2) -> enrich into a Document Intelligence report (S3) ->
chunk into a versioned chunk set (S4) -> embed into a versioned, validated
embedding asset (S5). Prints an embedding summary, demonstrates deterministic
dedupe, and shows lineage back to the chunk asset. Uses a local, deterministic,
dependency-free hash embedding provider, an in-memory Control Plane, and an
in-memory asset store.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_embedding.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.settings import ControlPlaneSettings  # noqa: E402
from domain.chunking import ChunkingEngine, ChunkingPolicy  # noqa: E402
from domain.control_plane import (  # noqa: E402
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    Lineage,
)
from domain.embedding import EmbeddingEngine, EmbeddingPolicy  # noqa: E402
from domain.intelligence import (  # noqa: E402
    DocumentIntelligenceEngine,
    IntelligencePolicy,
)
from domain.storage import InMemoryAssetStorage  # noqa: E402
from domain.sync import (  # noqa: E402
    LocalFileSystemConnector,
    RepositoryConnectorConfig,
    RepositorySynchronizer,
    SyncPolicy,
    register_repository,
)
from domain.transformation import (  # noqa: E402
    TransformationPipeline,
    TransformationPolicy,
)

TENANT_ID = "tenant-demo"

_PROCEDURE = """# Pump Maintenance Procedure

This maintenance procedure explains how to service the coolant pump safely.

## Safety

> Warning: disconnect power before servicing the unit.

## Steps

1. Stop the pump.
2. Drain the reservoir.
3. Inspect seal ABC-1 for wear.

## Torque Specifications

| Bolt | Torque (Nm) | Checked |
| --- | --- | --- |
| ABC-1 | 45 | 2024-01-02 |
| ABC-2 | 60 | 2024-03-11 |

```python
def start_pump() -> bool:
    return True
```
"""


def _seed(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "procedure.md").write_text(_PROCEDURE, encoding="utf-8")


def _ingest(db: ControlPlaneDatabase, storage: InMemoryAssetStorage, root: Path) -> str:
    """Run sync -> transform -> intelligence -> chunk and return the document id."""
    repository_id = register_repository(
        db,
        tenant_id=TENANT_ID,
        name="demo-repo",
        source_type="local_fs",
        uri=str(root),
    )
    connector = LocalFileSystemConnector(
        RepositoryConnectorConfig(
            repository_id=repository_id,
            tenant_id=TENANT_ID,
            name="demo-repo",
            connector_type="local_fs",
            root_uri=str(root),
        )
    )
    RepositorySynchronizer(db, connector, SyncPolicy()).synchronize(
        repository_id, TENANT_ID
    )
    with db.session() as session:
        document_id = (
            session.query(Document)
            .filter(Document.repository_id == repository_id)
            .one()
            .id
        )
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, TENANT_ID, connector.read_bytes("docs/procedure.md")
    )
    DocumentIntelligenceEngine(db, storage, IntelligencePolicy()).enrich(
        document_id, TENANT_ID
    )
    ChunkingEngine(db, storage, ChunkingPolicy()).chunk(document_id, TENANT_ID)
    return document_id


def main() -> None:
    """Run the sync -> transform -> intelligence -> chunk -> embed demo."""
    db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
    db.create_all()
    storage = InMemoryAssetStorage()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed(root)
        document_id = _ingest(db, storage, root)

        engine = EmbeddingEngine(db, storage, EmbeddingPolicy())
        result = engine.embed(document_id, TENANT_ID)

        doc = result.embedding_document
        print(f"{'=' * 72}\nEmbedding Set  ->  v{result.version}  ({result.storage_uri})")
        print(
            f"model={doc.model_name}  provider={doc.provider}  "
            f"dimension={doc.dimension}  metric={doc.distance_metric.value}"
        )
        print(
            f"embeddings={doc.embedding_count}  total_tokens={doc.total_tokens}  "
            f"batches={result.batch_count}  cost_estimate={result.cost_estimate}  "
            f"generation_ms={result.generation_ms}"
        )
        print("-" * 72)
        for record in doc.records:
            preview = ", ".join(f"{value:+.4f}" for value in record.values[:4])
            print(
                f"{record.embedding_id}  chunk={record.chunk_id}  "
                f"tokens={record.token_count:<4}  status={record.status.value:<8}  "
                f"[{preview}, ...]"
            )

        print(f"\n{'=' * 72}\nRe-running embedding to show deterministic dedupe...")
        repeat = engine.embed(document_id, TENANT_ID)
        print(f"created={repeat.created} (False means the identical embedding set was reused)")

        with db.session() as session:
            embedding_asset = (
                session.query(Asset)
                .filter(Asset.asset_type == AssetType.EMBEDDING)
                .one()
            )
            chunk_asset = (
                session.query(Asset).filter(Asset.asset_type == AssetType.CHUNKS).one()
            )
            lineage = (
                session.query(Lineage)
                .filter(Lineage.asset_id == embedding_asset.id)
                .one()
            )
            print(
                f"\nLineage: EMBEDDING({embedding_asset.id[:8]}) "
                f"--{lineage.relation}--> CHUNKS({chunk_asset.id[:8]})"
            )

    db.drop_all()
    print("\nDemo complete. The document now has a versioned, validated embedding asset.")


if __name__ == "__main__":
    main()

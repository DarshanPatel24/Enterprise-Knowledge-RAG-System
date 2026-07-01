"""Manual demo for the EKIE Intelligent Chunking Framework (EKIE-S4).

Runs the full local pipeline over a temp file: synchronize (S1) -> transform to
canonical Markdown (S2) -> enrich into a Document Intelligence report (S3) ->
chunk into a versioned, validated chunk set (S4). Prints a chunk summary and the
chunk JSON, then demonstrates deterministic dedupe and lineage. Uses an
in-memory Control Plane and in-memory asset store.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_chunking.py
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


def main() -> None:
    """Run the sync -> transform -> intelligence -> chunk demo end to end."""
    db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
    db.create_all()
    storage = InMemoryAssetStorage()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed(root)

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

        engine = ChunkingEngine(db, storage, ChunkingPolicy())
        result = engine.chunk(document_id, TENANT_ID)

        chunks = result.chunk_document
        print(f"{'=' * 72}\nChunk Set  ->  v{result.version}  ({result.storage_uri})")
        print(
            f"strategy={chunks.strategy.value}  chunks={chunks.chunk_count}  "
            f"total_tokens={chunks.total_tokens}"
        )
        print("-" * 72)
        for chunk in chunks.chunks:
            meta = chunk.metadata
            flags = "".join(
                [
                    "T" if meta.contains_table else "-",
                    "C" if meta.contains_code else "-",
                    "I" if meta.contains_image else "-",
                ]
            )
            print(
                f"{meta.chunk_id}  seq={meta.chunk_sequence:<2}  "
                f"tokens={meta.token_count:<4}  [{flags}]  {meta.breadcrumb}"
            )

        print(f"\n{'=' * 72}\nFull chunk JSON:")
        print(chunks.canonical_json().decode("utf-8"))

        print(f"\n{'=' * 72}\nRe-running chunking to show deterministic dedupe...")
        repeat = engine.chunk(document_id, TENANT_ID)
        print(f"created={repeat.created} (False means the identical chunk set was reused)")

        with db.session() as session:
            chunk_asset = (
                session.query(Asset).filter(Asset.asset_type == AssetType.CHUNKS).one()
            )
            intelligence_asset = (
                session.query(Asset)
                .filter(Asset.asset_type == AssetType.INTELLIGENCE)
                .one()
            )
            lineage = (
                session.query(Lineage)
                .filter(Lineage.asset_id == chunk_asset.id)
                .one()
            )
            print(
                f"\nLineage: CHUNKS({chunk_asset.id[:8]}) "
                f"--{lineage.relation}--> INTELLIGENCE({intelligence_asset.id[:8]})"
            )

    db.drop_all()
    print("\nDemo complete. The document now has a versioned, validated chunk asset.")


if __name__ == "__main__":
    main()

"""Manual demo for the EKIE Vector Publishing Framework (EKIE-S6).

Runs the full local pipeline over a temp file: synchronize (S1) -> transform to
canonical Markdown (S2) -> enrich into a Document Intelligence report (S3) ->
chunk (S4) -> embed (S5) -> publish vectors into the vector database (S6).
Prints a publish summary with collection schema, verified metadata, and lineage,
then demonstrates idempotent republishing. Uses a local, in-process vector
provider, an in-memory Control Plane, and an in-memory asset store.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_publishing.py
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
from domain.publishing import (  # noqa: E402
    PublishingPolicy,
    VectorPublishingEngine,
    default_provider_registry,
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
    """Run sync -> transform -> intelligence -> chunk -> embed; return doc id."""
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
    EmbeddingEngine(db, storage, EmbeddingPolicy()).embed(document_id, TENANT_ID)
    return document_id


def main() -> None:
    """Run the sync -> ... -> embed -> publish demo end to end."""
    db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
    db.create_all()
    storage = InMemoryAssetStorage()
    provider_registry = default_provider_registry()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed(root)
        document_id = _ingest(db, storage, root)

        engine = VectorPublishingEngine(
            db, storage, PublishingPolicy(), provider_registry=provider_registry
        )
        result = engine.publish(document_id, TENANT_ID)

        published = result.published_vector_set
        print(f"{'=' * 72}\nVector Set  ->  v{result.version}  ({result.storage_uri})")
        print(
            f"collection={result.collection}  provider={result.provider}  "
            f"dimension={result.dimension}  metric={published.distance_metric.value}"
        )
        print(
            f"vectors={result.vector_count}  verified={result.verified_count}  "
            f"batches={result.batch_count}  publish_ms={result.publish_ms}"
        )
        print("-" * 72)

        provider = provider_registry.get(result.provider)
        for record in published.records:
            stored = provider.fetch(result.collection, record.vector_id)
            section = stored.metadata.section_title if stored else None
            print(
                f"{record.vector_id}  chunk={record.chunk_id}  "
                f"state={record.state.value:<9}  section={section!r}"
            )

        print(f"\n{'=' * 72}\nRe-running publishing to show idempotency...")
        repeat = engine.publish(document_id, TENANT_ID)
        print(f"created={repeat.created} (False means the identical vector set was reused)")

        with db.session() as session:
            vector_asset = (
                session.query(Asset).filter(Asset.asset_type == AssetType.VECTOR).one()
            )
            embedding_asset = (
                session.query(Asset)
                .filter(Asset.asset_type == AssetType.EMBEDDING)
                .one()
            )
            lineage = (
                session.query(Lineage)
                .filter(Lineage.asset_id == vector_asset.id)
                .one()
            )
            print(
                f"\nLineage: VECTOR({vector_asset.id[:8]}) "
                f"--{lineage.relation}--> EMBEDDING({embedding_asset.id[:8]})"
            )

    db.drop_all()
    print("\nDemo complete. The document now has a verified, versioned vector asset.")


if __name__ == "__main__":
    main()

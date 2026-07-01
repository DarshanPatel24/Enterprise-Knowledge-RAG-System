"""Manual demo for the EKIE Document Intelligence Framework (EKIE-S3).

Runs the full local pipeline over temp files: synchronize (S1) -> transform to
canonical Markdown (S2) -> enrich into a versioned Document Intelligence report
(S3). Prints the report JSON and demonstrates deterministic dedupe and lineage.
Uses an in-memory Control Plane and in-memory asset store.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_intelligence.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.settings import ControlPlaneSettings  # noqa: E402
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

![Pump assembly diagram](images/pump.png)

Report issues to maintenance@example.com.

```python
def start_pump() -> bool:
    return True
```
"""


def _seed(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "procedure.md").write_text(_PROCEDURE, encoding="utf-8")


def main() -> None:
    """Run the sync -> transform -> intelligence demo end to end."""
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

        pipeline = TransformationPipeline(db, storage, TransformationPolicy())
        with db.session() as session:
            document_id = (
                session.query(Document)
                .filter(Document.repository_id == repository_id)
                .one()
                .id
            )
        pipeline.transform(document_id, TENANT_ID, connector.read_bytes("docs/procedure.md"))

        engine = DocumentIntelligenceEngine(db, storage, IntelligencePolicy())
        result = engine.enrich(document_id, TENANT_ID)

        print(f"{'=' * 72}\nDocument Intelligence Report  ->  v{result.version}")
        print(f"storage_uri={result.storage_uri}")
        print("-" * 72)
        print(result.report.canonical_json().decode("utf-8"))

        print(f"\n{'=' * 72}\nRe-running enrichment to show deterministic dedupe...")
        repeat = engine.enrich(document_id, TENANT_ID)
        print(f"created={repeat.created} (False means the identical report was reused)")

        with db.session() as session:
            intelligence_asset = (
                session.query(Asset)
                .filter(Asset.asset_type == AssetType.INTELLIGENCE)
                .one()
            )
            markdown_asset = (
                session.query(Asset)
                .filter(Asset.asset_type == AssetType.MARKDOWN)
                .one()
            )
            lineage = (
                session.query(Lineage)
                .filter(Lineage.asset_id == intelligence_asset.id)
                .one()
            )
            print(
                f"\nLineage: INTELLIGENCE({intelligence_asset.id[:8]}) "
                f"--{lineage.relation}--> MARKDOWN({markdown_asset.id[:8]})"
            )

    db.drop_all()
    print("\nDemo complete. The document now has a versioned intelligence asset.")


if __name__ == "__main__":
    main()

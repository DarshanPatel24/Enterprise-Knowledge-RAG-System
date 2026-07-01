"""Manual demo for the EKIE Document Transformation Framework (EKIE-S2).

Registers a repository, discovers files from a temp directory via the S1
synchronizer, then transforms each document into canonical Markdown and prints
the generated assets. Uses an in-memory Control Plane and in-memory asset store.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_transform.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config.settings import ControlPlaneSettings  # noqa: E402
from domain.control_plane import ControlPlaneDatabase, Document  # noqa: E402
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


def _seed(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "guide.md").write_text("# Guide\n\nStep one.\n\nStep two.\n")
    (root / "people.csv").write_text("name,role\nAda,Engineer\nGrace,Admiral\n")
    (root / "page.html").write_text(
        "<html lang='en'><head><title>Report</title></head>"
        "<body><h1>Quarterly Report</h1><p>All <strong>systems</strong> nominal.</p>"
        "<ul><li>Alpha</li><li>Beta</li></ul></body></html>"
    )


def main() -> None:
    """Run the transformation demo end to end."""
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
            documents = [
                (row.id, row.source_path)
                for row in session.query(Document)
                .filter(Document.repository_id == repository_id)
                .order_by(Document.source_path)
                .all()
            ]

        for document_id, source_path in documents:
            data = connector.read_bytes(source_path)
            result = pipeline.transform(document_id, TENANT_ID, data)
            print(f"\n{'=' * 70}\n{source_path}  ->  v{result.version} ({result.storage_uri})")
            print("-" * 70)
            print(result.markdown.rstrip())

        print(f"\n{'=' * 70}\nRe-running the first document to show deterministic dedupe...")
        document_id, source_path = documents[0]
        repeat = pipeline.transform(document_id, TENANT_ID, connector.read_bytes(source_path))
        print(f"created={repeat.created} (False means identical content was reused)")

    db.drop_all()
    print("\nDemo complete. Every document became versioned canonical Markdown.")


if __name__ == "__main__":
    main()

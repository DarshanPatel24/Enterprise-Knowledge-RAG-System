"""Manual demo for the EKIE Repository Synchronization Framework (EKIE-S1).

Runs a full lifecycle against a throwaway temp directory and an in-memory
Control Plane so you can watch create, modify, rename, and delete reconcile.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_sync.py
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
from domain.sync import (  # noqa: E402
    LocalFileSystemConnector,
    RepositoryConnectorConfig,
    RepositorySynchronizer,
    SyncPolicy,
    register_repository,
)

TENANT_ID = "tenant-demo"


def _print_events(title: str, events: list) -> None:
    print(f"\n=== {title} ===")
    for event in events:
        detail = f" ({event.detail})" if event.detail else ""
        path = event.source_path or ""
        prev = f" <- {event.previous_path}" if event.previous_path else ""
        print(f"  {event.event_type.value:24} {path}{prev}{detail}")


def _print_twins(db: ControlPlaneDatabase, repository_id: str) -> None:
    with db.session() as session:
        rows = (
            session.query(Document)
            .filter(Document.repository_id == repository_id)
            .order_by(Document.source_path)
            .all()
        )
        print("  Digital Twins:")
        for row in rows:
            print(f"    v{row.version} {str(row.status):9} {row.source_path}  id={row.id[:8]}")


def main() -> None:
    """Run the synchronization lifecycle demo."""
    db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
    db.create_all()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "policy.md").write_text("# Policy v1")
        (root / "readme.txt").write_text("hello world")

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
        synchronizer = RepositorySynchronizer(db, connector, SyncPolicy())

        result = synchronizer.synchronize(repository_id, TENANT_ID)
        _print_events("Initial scan", result.events)
        _print_twins(db, repository_id)

        (root / "readme.txt").write_text("hello world - updated")
        result = synchronizer.synchronize(repository_id, TENANT_ID)
        _print_events("After modifying readme.txt", result.events)
        _print_twins(db, repository_id)

        (root / "docs" / "policy.md").rename(root / "docs" / "policy-v2.md")
        result = synchronizer.synchronize(repository_id, TENANT_ID)
        _print_events("After renaming policy.md -> policy-v2.md", result.events)
        _print_twins(db, repository_id)

        (root / "readme.txt").unlink()
        result = synchronizer.synchronize(repository_id, TENANT_ID)
        _print_events("After deleting readme.txt", result.events)
        _print_twins(db, repository_id)

    db.drop_all()
    print("\nDemo complete. The renamed twin kept its id; the deleted twin is marked 'deleted'.")


if __name__ == "__main__":
    main()

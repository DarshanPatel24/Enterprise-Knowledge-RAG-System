"""Manual demo for the EKIE Workflow Orchestration engine (EKIE-S7).

Drives the full document ingestion pipeline as a checkpointed, resumable graph:
synchronize (S1, precursor) -> transform (S2) -> intelligence (S3) -> chunk (S4)
-> embed (S5) -> publish (S6), orchestrated by the S7 WorkflowOrchestrator.

Demonstrates:
  * a full run with per-stage records and lifecycle events;
  * idempotent replay from the stored checkpoint;
  * lineage-aware replay reconstructed from the Control Plane (no checkpoint);
  * dead-lettering when a stage cannot proceed.

Uses the deterministic local providers, an in-memory Control Plane, and an
in-memory asset store, so it runs fully offline.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_orchestration.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from composition import build_workflow_orchestrator  # noqa: E402
from config.settings import ControlPlaneSettings, EkieSettings  # noqa: E402
from domain.control_plane import (  # noqa: E402
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.orchestration import (  # noqa: E402
    InMemoryCheckpointer,
    WorkflowResult,
)
from domain.storage import InMemoryAssetStorage  # noqa: E402
from domain.sync import (  # noqa: E402
    LocalFileSystemConnector,
    RepositoryConnectorConfig,
    RepositorySynchronizer,
    SyncPolicy,
    register_repository,
)

TENANT_ID = "tenant-demo"

_PROCEDURE = """# Coolant Pump Maintenance Procedure

This maintenance procedure explains how the field technician services the
coolant pump safely, records the torque applied to each fastener, and validates
the repair before returning the unit to production.

## Safety

Disconnect power and confirm zero pressure before opening the housing.

## Steps

1. Stop the pump and isolate the circuit.
2. Drain the reservoir into the approved container.
3. Inspect seal ABC-1 for wear and replace it when scoring is visible.
"""


def _seed(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "procedure.md").write_text(_PROCEDURE, encoding="utf-8")


def _sync_document(db: ControlPlaneDatabase, root: Path) -> tuple[str, bytes]:
    """Run the sync precursor and return the emitted document id and its bytes."""
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
    return document_id, connector.read_bytes("docs/procedure.md")


def _empty_document(db: ControlPlaneDatabase) -> str:
    """Register a document with no source content to demonstrate dead-lettering."""
    with db.session() as session:
        repo = Repository(
            tenant_id=TENANT_ID,
            name="empty-repo",
            source_type="local_fs",
            uri="local://empty",
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repo)
        session.flush()
        document = Document(
            repository_id=repo.id,
            tenant_id=TENANT_ID,
            source_path="docs/missing.md",
            content_hash="seed",
            classification_clearance="internal",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


def _print_result(title: str, result: WorkflowResult) -> None:
    print(f"\n=== {title} ===")
    print(f"status={result.status.value} correlation_id={result.correlation_id}")
    for record in result.records:
        print(
            f"  {record.stage.value:<13} v{record.version} "
            f"created={record.created} attempts={record.attempts}"
        )
    if result.failure is not None:
        print(
            f"  dead-letter at {result.failure.stage.value}: "
            f"{result.failure.error_type} ({result.failure.message})"
        )
    print("  events: " + " -> ".join(event.event_type.value for event in result.events))


def main() -> None:
    """Run the orchestration demo end to end."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _seed(root)

        settings = EkieSettings()
        db = ControlPlaneDatabase(
            ControlPlaneSettings(url="sqlite+pysqlite:///:memory:")
        )
        db.create_all()
        storage = InMemoryAssetStorage()

        document_id, source_bytes = _sync_document(db, root)
        checkpointer = InMemoryCheckpointer()
        orchestrator = build_workflow_orchestrator(
            settings, db, storage, checkpointer=checkpointer
        )

        first = orchestrator.run(
            document_id, TENANT_ID, source_bytes=source_bytes, mime_type="text/markdown"
        )
        _print_result("Full ingestion run", first)

        replay = orchestrator.resume(document_id, TENANT_ID)
        _print_result("Idempotent replay from checkpoint", replay)

        fresh = build_workflow_orchestrator(
            settings, db, storage, checkpointer=InMemoryCheckpointer()
        )
        reconciled = fresh.reconcile(document_id, TENANT_ID)
        print("\n=== Lineage-aware reconciliation (no checkpoint) ===")
        print(
            f"status={reconciled.status.value} "
            f"completed={[s.value for s in reconciled.completed_stages]}"
        )

        dead_document = _empty_document(db)
        dead = orchestrator.resume(dead_document, TENANT_ID)
        _print_result("Dead-letter (missing source)", dead)


if __name__ == "__main__":
    main()

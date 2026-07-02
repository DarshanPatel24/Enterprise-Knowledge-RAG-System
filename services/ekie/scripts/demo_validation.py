"""Manual demo for the EKIE Testing, Validation and Deployment Readiness suite (EKIE-S9).

Demonstrates the S9 validation and readiness capabilities end to end:
  * running the full ingestion pipeline over a document;
  * pipeline-level validation of workflow, lineage, chunks, embeddings, vectors;
  * a small load run reporting success rate, throughput, and latency percentiles;
  * failure simulation that dead-letters a workflow at an injected stage;
  * deployment / HA / DR readiness assessment from configuration;
  * building the EKRE handoff readiness package for a published document.

Runs fully offline using deterministic, dependency-free components and an
in-memory Control Plane and object store.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_validation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from composition import build_pipeline_engines, build_pipeline_validator  # noqa: E402
from config.settings import ControlPlaneSettings, EkieSettings  # noqa: E402
from domain.control_plane import (  # noqa: E402
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.orchestration import (  # noqa: E402
    OrchestrationPolicy,
    StageName,
    WorkflowOrchestrator,
)
from domain.storage import InMemoryAssetStorage  # noqa: E402
from domain.validation import (  # noqa: E402
    DocumentLoadSpec,
    assess_readiness,
    build_handoff_package,
    failing_stages,
    run_load,
)

_TENANT = "tenant-a"
_SOURCE = (
    b"# Onboarding Procedure\n\n"
    b"This procedure describes how new engineers set up their local development "
    b"environment, install the required tooling, and validate their first build "
    b"before requesting access to production systems.\n\n"
    b"## Steps\n\n"
    b"Follow each step carefully and confirm the expected output before moving on "
    b"to the next one to avoid configuration drift across the whole team.\n"
)


def _rule(title: str) -> None:
    print(f"\n=== {title} ===")


def _fresh_db() -> ControlPlaneDatabase:
    db = ControlPlaneDatabase(
        ControlPlaneSettings(url="sqlite+pysqlite:///:memory:")
    )
    db.create_all()
    return db


def _register_document(db: ControlPlaneDatabase, name: str) -> str:
    with db.session() as session:
        repo = Repository(
            tenant_id=_TENANT,
            name=name,
            source_type="local_fs",
            uri="local://repo",
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repo)
        session.flush()
        document = Document(
            repository_id=repo.id,
            tenant_id=_TENANT,
            source_path="docs/onboarding.md",
            content_hash="demo-hash",
            classification_clearance="confidential",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


def _orchestrator(
    db: ControlPlaneDatabase,
    storage: InMemoryAssetStorage,
    *,
    fail_at: StageName | None = None,
) -> WorkflowOrchestrator:
    settings = EkieSettings()
    engines = build_pipeline_engines(settings, db, storage)
    stages = failing_stages(fail_at) if fail_at is not None else None
    return WorkflowOrchestrator(
        db,
        engines,
        OrchestrationPolicy(max_attempts_per_stage=1),
        stages=stages,
    )


def _demo_pipeline_validation() -> None:
    _rule("Pipeline validation (S9-1, S9-2)")
    db = _fresh_db()
    storage = InMemoryAssetStorage()
    orchestrator = _orchestrator(db, storage)
    document_id = _register_document(db, "repo-validate")
    result = orchestrator.run(document_id, _TENANT, source_bytes=_SOURCE)
    print(f"workflow status: {result.status.value}")

    report = build_pipeline_validator(db, storage).validate(result)
    print(f"validation passed: {report.passed}")
    for finding in report.findings:
        print(f"  [{finding.severity.value:7}] {finding.check}: {finding.message}")


def _demo_load() -> None:
    _rule("Load, throughput and latency (S9-3)")
    db = _fresh_db()
    storage = InMemoryAssetStorage()
    orchestrator = _orchestrator(db, storage)
    specs = [
        DocumentLoadSpec(
            document_id=_register_document(db, f"repo-load-{index}"),
            tenant_id=_TENANT,
            source_bytes=_SOURCE,
        )
        for index in range(5)
    ]
    report = run_load(orchestrator, specs)
    print(f"total={report.total} succeeded={report.succeeded} "
          f"dead_lettered={report.dead_lettered}")
    print(f"success_rate={report.success_rate:.2f} "
          f"p50={report.p50_seconds * 1000:.2f}ms "
          f"p95={report.p95_seconds * 1000:.2f}ms")


def _demo_failure_simulation() -> None:
    _rule("Failure simulation (S9-3)")
    db = _fresh_db()
    storage = InMemoryAssetStorage()
    orchestrator = _orchestrator(db, storage, fail_at=StageName.EMBED)
    document_id = _register_document(db, "repo-fault")
    result = orchestrator.run(document_id, _TENANT, source_bytes=_SOURCE)
    print(f"workflow status: {result.status.value}")
    if result.failure is not None:
        print(f"failed stage: {result.failure.stage.value} "
              f"({result.failure.error_type})")


def _demo_readiness() -> None:
    _rule("Deployment / HA / DR readiness (S9-4)")
    report = assess_readiness(EkieSettings())
    print(f"readiness passed: {report.passed}")
    for finding in report.findings:
        print(f"  [{finding.severity.value:7}] {finding.check}: {finding.message}")


def _demo_handoff() -> None:
    _rule("EKRE handoff readiness package (S9-5)")
    db = _fresh_db()
    storage = InMemoryAssetStorage()
    orchestrator = _orchestrator(db, storage)
    document_id = _register_document(db, "repo-handoff")
    result = orchestrator.run(document_id, _TENANT, source_bytes=_SOURCE)
    package = build_handoff_package(db, storage, result)
    print(f"collection={package.collection} model={package.model_name} "
          f"provider={package.provider}")
    print(f"dimension={package.dimension} vectors={package.vector_count} "
          f"chunks={package.chunk_count}")
    print(f"classification={package.classification_clearance} "
          f"validation_passed={package.validation_passed}")
    print(f"lineage={', '.join(package.lineage_relations)}")


def main() -> None:
    """Run all EKIE-S9 validation and readiness demonstrations."""
    _demo_pipeline_validation()
    _demo_load()
    _demo_failure_simulation()
    _demo_readiness()
    _demo_handoff()


if __name__ == "__main__":
    main()

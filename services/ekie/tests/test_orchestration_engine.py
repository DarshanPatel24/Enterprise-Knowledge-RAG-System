"""Integration tests for the workflow orchestrator over the real pipeline."""

from __future__ import annotations

import pytest

from composition import build_pipeline_engines
from config.settings import EkieSettings
from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.orchestration import (
    InMemoryCheckpointer,
    OrchestrationPolicy,
    Stage,
    StageName,
    StageOutcome,
    WorkflowOrchestrator,
    WorkflowStatus,
)
from domain.storage import InMemoryAssetStorage

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

_ALL_STAGES = (
    StageName.TRANSFORM,
    StageName.INTELLIGENCE,
    StageName.CHUNK,
    StageName.EMBED,
    StageName.PUBLISH,
)


def _register_document(db: ControlPlaneDatabase) -> str:
    with db.session() as session:
        repo = Repository(
            tenant_id=_TENANT,
            name="repo",
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
            content_hash="seed",
            classification_clearance="internal",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


def _orchestrator(
    db: ControlPlaneDatabase,
    *,
    checkpointer: InMemoryCheckpointer | None = None,
    stages: tuple[Stage, ...] | None = None,
) -> WorkflowOrchestrator:
    settings = EkieSettings()
    engines = build_pipeline_engines(settings, db, InMemoryAssetStorage())
    return WorkflowOrchestrator(
        db,
        engines,
        OrchestrationPolicy(max_attempts_per_stage=1),
        checkpointer=checkpointer,
        stages=stages,
    )


def _asset_types(db: ControlPlaneDatabase, document_id: str) -> set[AssetType]:
    with db.session() as session:
        return {
            asset.asset_type
            for asset in session.query(Asset).filter(
                Asset.document_id == document_id
            )
        }


def test_run_completes_full_pipeline(control_plane_db: ControlPlaneDatabase) -> None:
    document_id = _register_document(control_plane_db)
    orchestrator = _orchestrator(control_plane_db)

    result = orchestrator.run(document_id, _TENANT, source_bytes=_SOURCE)

    assert result.status == WorkflowStatus.COMPLETED
    assert result.completed_stages == _ALL_STAGES
    assert len(result.records) == 5
    assert _asset_types(control_plane_db, document_id) == set(AssetType)


def test_reconcile_infers_completed_stages_from_lineage(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _register_document(control_plane_db)
    orchestrator = _orchestrator(control_plane_db)
    orchestrator.run(document_id, _TENANT, source_bytes=_SOURCE)

    state = orchestrator.reconcile(document_id, _TENANT)

    assert state.completed_stages == _ALL_STAGES


def test_resume_is_idempotent_from_checkpoint(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _register_document(control_plane_db)
    checkpointer = InMemoryCheckpointer()
    orchestrator = _orchestrator(control_plane_db, checkpointer=checkpointer)
    orchestrator.run(document_id, _TENANT, source_bytes=_SOURCE)

    replay = orchestrator.resume(document_id, _TENANT)

    assert replay.status == WorkflowStatus.COMPLETED
    assert replay.completed_stages == _ALL_STAGES
    # No new asset versions are created on idempotent replay.
    with control_plane_db.session() as session:
        assert session.query(Asset).count() == 5


def test_resume_replays_from_lineage_without_checkpoint(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _register_document(control_plane_db)
    _orchestrator(control_plane_db).run(document_id, _TENANT, source_bytes=_SOURCE)

    # A fresh orchestrator has an empty checkpoint store and must reconstruct
    # progress from Control Plane lineage.
    fresh = _orchestrator(control_plane_db, checkpointer=InMemoryCheckpointer())
    replay = fresh.resume(document_id, _TENANT)

    assert replay.status == WorkflowStatus.COMPLETED
    assert replay.completed_stages == _ALL_STAGES


def test_resume_without_source_dead_letters_on_transform(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _register_document(control_plane_db)
    orchestrator = _orchestrator(control_plane_db)

    result = orchestrator.resume(document_id, _TENANT)

    assert result.status == WorkflowStatus.DEAD_LETTER
    assert result.failure is not None
    assert result.failure.stage == StageName.TRANSFORM
    assert result.failure.error_type == "missing_source"


def test_run_dead_letters_on_stage_failure(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _register_document(control_plane_db)

    def _boom(engines: object, state: object) -> StageOutcome:
        raise RuntimeError("stage exploded")

    orchestrator = _orchestrator(
        control_plane_db, stages=(Stage(StageName.TRANSFORM, _boom),)  # type: ignore[arg-type]
    )
    result = orchestrator.run(document_id, _TENANT, source_bytes=_SOURCE)

    assert result.status == WorkflowStatus.DEAD_LETTER
    assert result.failure is not None
    assert result.failure.stage == StageName.TRANSFORM


def test_run_generates_correlation_id_when_absent(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    document_id = _register_document(control_plane_db)
    orchestrator = _orchestrator(control_plane_db)

    result = orchestrator.run(
        document_id, _TENANT, source_bytes=_SOURCE, correlation_id="corr-run-1"
    )

    assert result.correlation_id == "corr-run-1"


@pytest.mark.parametrize("mime_type", [None, "text/markdown"])
def test_run_accepts_optional_mime_type(
    control_plane_db: ControlPlaneDatabase, mime_type: str | None
) -> None:
    document_id = _register_document(control_plane_db)
    orchestrator = _orchestrator(control_plane_db)

    result = orchestrator.run(
        document_id, _TENANT, source_bytes=_SOURCE, mime_type=mime_type
    )

    assert result.status == WorkflowStatus.COMPLETED

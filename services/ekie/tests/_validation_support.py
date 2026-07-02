"""Shared helpers for EKIE-S9 validation tests.

Builds a pipeline harness where the orchestrator and the validator share a single
object-storage instance so read-back validation observes the assets the pipeline
wrote. Not collected by pytest (module name is not ``test_*``).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from composition import build_pipeline_engines
from config.settings import EkieSettings
from domain.control_plane import (
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.orchestration import (
    OrchestrationPolicy,
    Stage,
    WorkflowOrchestrator,
)
from domain.storage import InMemoryAssetStorage
from domain.validation import PipelineValidator

TENANT = "tenant-a"
SOURCE = (
    b"# Onboarding Procedure\n\n"
    b"This procedure describes how new engineers set up their local development "
    b"environment, install the required tooling, and validate their first build "
    b"before requesting access to production systems.\n\n"
    b"## Steps\n\n"
    b"Follow each step carefully and confirm the expected output before moving on "
    b"to the next one to avoid configuration drift across the whole team.\n"
)


def register_document(
    db: ControlPlaneDatabase,
    *,
    classification: str = "internal",
    content_hash: str = "seed",
) -> str:
    """Register an active repository and document, returning the document id."""
    with db.session() as session:
        repo = Repository(
            tenant_id=TENANT,
            name=f"repo-{uuid.uuid4().hex[:8]}",
            source_type="local_fs",
            uri="local://repo",
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repo)
        session.flush()
        document = Document(
            repository_id=repo.id,
            tenant_id=TENANT,
            source_path="docs/onboarding.md",
            content_hash=content_hash,
            classification_clearance=classification,
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


@dataclass
class PipelineHarness:
    """A shared-storage orchestrator plus validator for read-back checks."""

    db: ControlPlaneDatabase
    storage: InMemoryAssetStorage
    orchestrator: WorkflowOrchestrator
    validator: PipelineValidator


def build_harness(
    db: ControlPlaneDatabase,
    *,
    stages: tuple[Stage, ...] | None = None,
    max_attempts: int = 1,
) -> PipelineHarness:
    """Build a harness whose orchestrator and validator share one storage."""
    settings = EkieSettings()
    storage = InMemoryAssetStorage()
    engines = build_pipeline_engines(settings, db, storage)
    orchestrator = WorkflowOrchestrator(
        db,
        engines,
        OrchestrationPolicy(max_attempts_per_stage=max_attempts),
        stages=stages,
    )
    return PipelineHarness(
        db=db,
        storage=storage,
        orchestrator=orchestrator,
        validator=PipelineValidator(db, storage),
    )

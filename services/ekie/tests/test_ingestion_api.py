"""API tests for the ingestion router wired to the composition root."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import AppResources, get_resources
from api.middleware import TENANT_HEADER
from composition import build_pipeline_engines
from config.settings import ControlPlaneSettings, EkieSettings
from domain.control_plane import (
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.orchestration import OrchestrationPolicy, WorkflowOrchestrator
from domain.storage import InMemoryAssetStorage

_TENANT = "tenant-a"
_SOURCE = (
    b"# Runbook\n\n"
    b"This runbook explains how the on-call engineer responds to a paging alert, "
    b"triages the affected service, and escalates when the incident is not "
    b"resolved within the agreed response window.\n"
)


@pytest.fixture
def resources() -> AppResources:
    settings = EkieSettings()
    db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
    db.create_all()
    storage = InMemoryAssetStorage()
    orchestrator = WorkflowOrchestrator(
        db,
        build_pipeline_engines(settings, db, storage),
        OrchestrationPolicy(max_attempts_per_stage=1),
    )
    return AppResources(
        settings=settings, db=db, storage=storage, orchestrator=orchestrator
    )


@pytest.fixture
def app(resources: AppResources) -> Iterator[FastAPI]:
    application = create_app()
    application.dependency_overrides[get_resources] = lambda: resources
    yield application
    application.dependency_overrides.clear()


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
            source_path="docs/runbook.md",
            content_hash="seed",
            classification_clearance="internal",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


async def test_ingest_runs_full_pipeline(
    app: FastAPI, resources: AppResources
) -> None:
    document_id = _register_document(resources.db)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/v1/documents/{document_id}/ingest",
            content=_SOURCE,
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["completed_stages"]) == 5
    assert body["failure"] is None


async def test_ingest_requires_tenant_header(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/v1/documents/doc-x/ingest", content=_SOURCE)

    assert response.status_code == 400


async def test_ingest_unknown_document_dead_letters(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/v1/documents/missing-doc/ingest",
            content=_SOURCE,
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "dead_letter"
    assert body["failure"]["error_type"] == "not_found"


async def test_workflow_status_reports_completed_after_ingest(
    app: FastAPI, resources: AppResources
) -> None:
    document_id = _register_document(resources.db)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/v1/documents/{document_id}/ingest",
            content=_SOURCE,
            headers={TENANT_HEADER: _TENANT},
        )
        response = await client.get(
            f"/v1/documents/{document_id}/workflow",
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["completed_stages"]) == 5


async def test_workflow_status_pending_for_unknown_document(app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/v1/documents/nope/workflow", headers={TENANT_HEADER: _TENANT}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["completed_stages"] == []


async def test_replay_is_idempotent_after_ingest(
    app: FastAPI, resources: AppResources
) -> None:
    document_id = _register_document(resources.db)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/v1/documents/{document_id}/ingest",
            content=_SOURCE,
            headers={TENANT_HEADER: _TENANT},
        )
        response = await client.post(
            f"/v1/documents/{document_id}/replay",
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

"""API tests for the ingestion router wired to the composition root."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

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
from domain.jobs import JobQueueStore, SourceStore
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
    base = EkieSettings(_env_file=None)
    settings = base.model_copy(
        update={
            "intelligence": base.intelligence.model_copy(
                update={"enable_llm_analysis": False}
            ),
            "embedding": base.embedding.model_copy(
                update={"provider": "local", "dimension": 4096}
            ),
            "publishing": base.publishing.model_copy(update={"provider": "local"}),
            "orchestration": base.orchestration.model_copy(
                update={"runner": "sequential"}
            ),
        }
    )
    db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
    db.create_all()
    storage = InMemoryAssetStorage()
    orchestrator = WorkflowOrchestrator(
        db,
        build_pipeline_engines(settings, db, storage),
        OrchestrationPolicy(max_attempts_per_stage=1),
    )
    return AppResources(
        settings=settings,
        db=db,
        storage=storage,
        orchestrator=orchestrator,
        job_queue=JobQueueStore(db),
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


def _register_repository(
    db: ControlPlaneDatabase,
    *,
    uri: str,
    source_type: str = "local_fs",
) -> str:
    with db.session() as session:
        repository = Repository(
            tenant_id=_TENANT,
            name=f"repo-{uuid4().hex[:8]}",
            source_type=source_type,
            uri=uri,
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repository)
        session.flush()
        return repository.id


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


async def test_repository_ingest_syncs_and_ingests_all_documents(
    app: FastAPI,
    resources: AppResources,
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A\n\nRunbook A", encoding="utf-8")
    (docs / "b.txt").write_text("Runbook B", encoding="utf-8")
    repository_id = _register_repository(resources.db, uri=str(tmp_path))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/v1/repositories/{repository_id}/ingest",
            json={"sync_before_ingest": True},
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["repository_id"] == repository_id
    assert body["synchronized"] is True
    assert body["attempted"] == 2
    assert body["completed"] == 2
    assert body["dead_lettered"] == 0
    assert body["errors"] == []
    assert len(body["results"]) == 2
    assert all(result["status"] == "completed" for result in body["results"])


async def test_repository_ingest_returns_404_for_missing_repository(
    app: FastAPI,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/v1/repositories/missing/ingest",
            json={"sync_before_ingest": False},
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 404


async def test_delete_document_removes_row_and_returns_summary(
    app: FastAPI,
    resources: AppResources,
) -> None:
    document_id = _register_document(resources.db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/v1/documents/{document_id}",
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["row_deleted"] is True
    assert body["vectors_deleted"] == 0
    assert body["message"] == "document deleted"
    with resources.db.session() as session:
        assert session.get(Document, document_id) is None


async def test_delete_document_unknown_returns_404(
    app: FastAPI,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            "/v1/documents/does-not-exist",
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 404


def _enable_async(app: FastAPI, resources: AppResources) -> AppResources:
    """Rebind the app to resources with async ingestion enabled."""
    async_settings = resources.settings.model_copy(
        update={
            "ingestion": resources.settings.ingestion.model_copy(
                update={"async_enabled": True}
            )
        }
    )
    async_resources = replace(resources, settings=async_settings)
    app.dependency_overrides[get_resources] = lambda: async_resources
    return async_resources


async def test_async_ingest_enqueues_job_and_returns_202(
    app: FastAPI,
    resources: AppResources,
) -> None:
    async_resources = _enable_async(app, resources)
    document_id = _register_document(resources.db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/v1/documents/{document_id}/ingest",
            content=_SOURCE,
            headers={
                TENANT_HEADER: _TENANT,
                "Content-Type": "application/octet-stream",
            },
        )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["kind"] == "ingest"
    assert body["document_id"] == document_id
    assert body["status_url"] == f"/v1/documents/{document_id}/job"

    # Source bytes are persisted for the worker.
    assert SourceStore(async_resources.db).load(_TENANT, document_id) == _SOURCE

    # The job-status endpoint reports the queued job.
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        status_response = await client.get(
            f"/v1/documents/{document_id}/job",
            headers={TENANT_HEADER: _TENANT},
        )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "queued"


async def test_async_ingest_sync_override_runs_inline(
    app: FastAPI,
    resources: AppResources,
) -> None:
    _enable_async(app, resources)
    document_id = _register_document(resources.db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/v1/documents/{document_id}/ingest?sync=true",
            content=_SOURCE,
            headers={
                TENANT_HEADER: _TENANT,
                "Content-Type": "application/octet-stream",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert "completed_stages" in body


async def test_document_job_status_unknown_returns_404(
    app: FastAPI,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/v1/documents/missing/job",
            headers={TENANT_HEADER: _TENANT},
        )

    assert response.status_code == 404


async def test_repository_ingest_hard_deletes_removed_document(
    app: FastAPI,
    resources: AppResources,
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    file_path = docs / "delete-me.md"
    file_path.write_text("# delete me", encoding="utf-8")
    repository_id = _register_repository(resources.db, uri=str(tmp_path))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        first = await client.post(
            f"/v1/repositories/{repository_id}/ingest",
            json={"sync_before_ingest": True},
            headers={TENANT_HEADER: _TENANT},
        )
    assert first.status_code == 200

    with resources.db.session() as session:
        doc = (
            session.query(Document)
            .filter(
                Document.repository_id == repository_id,
                Document.tenant_id == _TENANT,
                Document.source_path == "docs/delete-me.md",
            )
            .first()
        )
        assert doc is not None
        deleted_document_id = doc.id

    # Removing the source file should hard-delete the document on next sync.
    file_path.unlink()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        second = await client.post(
            f"/v1/repositories/{repository_id}/ingest",
            json={"sync_before_ingest": True},
            headers={TENANT_HEADER: _TENANT},
        )

    assert second.status_code == 200
    with resources.db.session() as session:
        assert session.get(Document, deleted_document_id) is None

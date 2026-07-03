"""Ingestion API: run and inspect document ingestion workflows.

Exposes the composition-root-built :class:`WorkflowOrchestrator` over REST. All
requests are tenant-scoped via the ``X-Tenant-ID`` header (bound by the
correlation middleware) and correlation-tagged via ``X-Correlation-ID``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from api.dependencies import (
    AppResources,
    get_control_plane,
    get_orchestrator,
    get_resources,
    require_tenant,
)
from domain.control_plane import (
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
)
from domain.observability import get_correlation_id
from domain.orchestration import (
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowState,
    WorkflowStatus,
)
from domain.orchestration.state import StageRecord
from domain.publishing import VectorCleanupError, VectorCleanupService, cleanup_provider_registry
from domain.sync import (
    RepositoryConnector,
    RepositoryConnectorConfig,
    RepositorySynchronizer,
    SyncEventType,
    SyncPolicy,
    default_registry,
)

router = APIRouter(prefix="/v1/documents", tags=["ingestion"])
repository_router = APIRouter(prefix="/v1/repositories", tags=["ingestion"])

TenantId = Annotated[str, Depends(require_tenant)]
Orchestrator = Annotated[WorkflowOrchestrator, Depends(get_orchestrator)]
ControlPlane = Annotated[ControlPlaneDatabase, Depends(get_control_plane)]
Resources = Annotated[AppResources, Depends(get_resources)]


class StageRecordResponse(BaseModel):
    """A completed stage in an ingestion workflow."""

    stage: str
    version: int
    created: bool
    content_hash: str
    attempts: int
    metrics: dict[str, int | float | str] = Field(default_factory=dict)


class FailureResponse(BaseModel):
    """The failure that dead-lettered a workflow."""

    stage: str
    error_type: str
    message: str
    attempts: int


class WorkflowResponse(BaseModel):
    """Summary of an ingestion workflow's outcome."""

    document_id: str
    tenant_id: str
    correlation_id: str
    status: str
    completed_stages: list[str]
    records: list[StageRecordResponse]
    failure: FailureResponse | None = None


class RepositoryIngestRequest(BaseModel):
    """Controls repository-level synchronization and ingestion behavior."""

    sync_before_ingest: bool = True
    document_ids: tuple[str, ...] = ()
    max_documents: int | None = Field(default=None, ge=1)


class RepositoryIngestError(BaseModel):
    """A document-level error encountered while ingesting a repository."""

    document_id: str
    source_path: str
    message: str


class RepositoryIngestResponse(BaseModel):
    """Summary and per-document outcomes for repository-level ingestion."""

    repository_id: str
    tenant_id: str
    synchronized: bool
    attempted: int
    completed: int
    dead_lettered: int
    errors: list[RepositoryIngestError] = Field(default_factory=list)
    results: list[WorkflowResponse] = Field(default_factory=list)


class VectorDeleteResponse(BaseModel):
    """Outcome of purging vectors for a single document."""

    document_id: str
    tenant_id: str
    deleted_count: int
    provider: str | None = None
    collection: str | None = None
    message: str


def _records(records: tuple[StageRecord, ...]) -> list[StageRecordResponse]:
    """Map stage records into their response representation."""
    return [
        StageRecordResponse(
            stage=record.stage.value,
            version=record.version,
            created=record.created,
            content_hash=record.content_hash,
            attempts=record.attempts,
            metrics=record.metrics,
        )
        for record in records
    ]


def _result_response(result: WorkflowResult) -> WorkflowResponse:
    """Map a workflow result into its response representation."""
    failure = (
        None
        if result.failure is None
        else FailureResponse(
            stage=result.failure.stage.value,
            error_type=result.failure.error_type,
            message=result.failure.message,
            attempts=result.failure.attempts,
        )
    )
    return WorkflowResponse(
        document_id=result.document_id,
        tenant_id=result.tenant_id,
        correlation_id=result.correlation_id,
        status=result.status.value,
        completed_stages=[stage.value for stage in result.completed_stages],
        records=_records(result.records),
        failure=failure,
    )


def _state_response(state: WorkflowState) -> WorkflowResponse:
    """Map a reconciled workflow state into its response representation."""
    return WorkflowResponse(
        document_id=state.document_id,
        tenant_id=state.tenant_id,
        correlation_id=state.correlation_id,
        status=state.status.value,
        completed_stages=[stage.value for stage in state.completed_stages],
        records=_records(state.records),
    )


def _apply_status(response: Response, result_status: WorkflowStatus) -> None:
    """Set the HTTP status from the workflow outcome."""
    if result_status == WorkflowStatus.DEAD_LETTER:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    else:
        response.status_code = status.HTTP_200_OK


def _load_repository(
    db: ControlPlaneDatabase, repository_id: str, tenant_id: str
) -> Repository | None:
    """Return the tenant-scoped repository, if it exists."""
    with db.session() as session:
        repository = session.get(Repository, repository_id)
        if repository is None or repository.tenant_id != tenant_id:
            return None
        session.expunge(repository)
        return repository


def _repository_connector(repository: Repository) -> RepositoryConnector:
    """Build the configured connector instance for a repository."""
    config = RepositoryConnectorConfig(
        repository_id=repository.id,
        tenant_id=repository.tenant_id,
        name=repository.name,
        connector_type=repository.source_type,
        root_uri=repository.uri,
    )
    return default_registry().create(config)


def _repository_documents(
    db: ControlPlaneDatabase,
    repository_id: str,
    tenant_id: str,
    *,
    document_ids: tuple[str, ...],
    max_documents: int | None,
) -> list[Document]:
    """Return active repository documents in deterministic source-path order."""
    with db.session() as session:
        query = (
            session.query(Document)
            .filter(
                Document.repository_id == repository_id,
                Document.tenant_id == tenant_id,
                Document.status == DocumentStatus.ACTIVE,
            )
            .order_by(Document.source_path.asc())
        )
        if document_ids:
            query = query.filter(Document.id.in_(document_ids))
        rows = query.all()
        for row in rows:
            session.expunge(row)
    if max_documents is not None:
        return rows[:max_documents]
    return rows


def _vector_cleanup_service(resources: AppResources) -> VectorCleanupService:
    """Build a vector cleanup service from active app resources."""
    qdrant = resources.settings.qdrant
    providers = cleanup_provider_registry(
        qdrant_host=qdrant.host,
        qdrant_port=qdrant.port,
        qdrant_timeout_seconds=qdrant.request_timeout_seconds,
    )
    return VectorCleanupService(resources.db, resources.storage, providers)


@router.post("/{document_id}/ingest", response_model=WorkflowResponse)
async def ingest_document(
    document_id: str,
    request: Request,
    response: Response,
    tenant_id: TenantId,
    orchestrator: Orchestrator,
    mime_type: str | None = None,
    intelligence_provider: str | None = None,
    intelligence_model: str | None = None,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
) -> WorkflowResponse:
    """Run the full ingestion workflow for a synced document from raw bytes."""
    source_bytes = await request.body()
    result = orchestrator.run(
        document_id,
        tenant_id,
        source_bytes=source_bytes,
        mime_type=mime_type,
        correlation_id=get_correlation_id(),
        intelligence_provider=intelligence_provider,
        intelligence_model=intelligence_model,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
    )
    _apply_status(response, result.status)
    return _result_response(result)


@router.post("/{document_id}/replay", response_model=WorkflowResponse)
async def replay_document(
    document_id: str,
    request: Request,
    response: Response,
    tenant_id: TenantId,
    orchestrator: Orchestrator,
    intelligence_provider: str | None = None,
    intelligence_model: str | None = None,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
) -> WorkflowResponse:
    """Resume or replay a workflow from its checkpoint or Control Plane lineage."""
    body = await request.body()
    source_bytes = body if body else None
    result = orchestrator.resume(
        document_id,
        tenant_id,
        source_bytes=source_bytes,
        correlation_id=get_correlation_id(),
        intelligence_provider=intelligence_provider,
        intelligence_model=intelligence_model,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
    )
    _apply_status(response, result.status)
    return _result_response(result)


@router.get("/{document_id}/workflow", response_model=WorkflowResponse)
async def workflow_status(
    document_id: str,
    tenant_id: TenantId,
    orchestrator: Orchestrator,
    _db: ControlPlane,
) -> WorkflowResponse:
    """Return the reconciled workflow status inferred from Control Plane lineage."""
    state = orchestrator.reconcile(document_id, tenant_id)
    return _state_response(state)


@router.delete("/{document_id}/vectors", response_model=VectorDeleteResponse)
async def purge_document_vectors(
    document_id: str,
    tenant_id: TenantId,
    resources: Resources,
) -> VectorDeleteResponse:
    """Delete published vectors for a document, typically after source deletion."""
    cleaner = _vector_cleanup_service(resources)
    try:
        result = cleaner.purge_document_vectors(document_id, tenant_id)
    except VectorCleanupError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    if result is None:
        return VectorDeleteResponse(
            document_id=document_id,
            tenant_id=tenant_id,
            deleted_count=0,
            message="no published vectors found",
        )
    return VectorDeleteResponse(
        document_id=document_id,
        tenant_id=tenant_id,
        deleted_count=result.deleted_count,
        provider=result.provider,
        collection=result.collection,
        message="vectors deleted",
    )


@repository_router.post("/{repository_id}/ingest", response_model=RepositoryIngestResponse)
async def ingest_repository(
    repository_id: str,
    request: RepositoryIngestRequest,
    tenant_id: TenantId,
    resources: Resources,
    orchestrator: Orchestrator,
    intelligence_provider: str | None = None,
    intelligence_model: str | None = None,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
) -> RepositoryIngestResponse:
    """Synchronize a repository and ingest its active documents in one call."""
    db = resources.db
    repository = _load_repository(db, repository_id, tenant_id)
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"repository {repository_id!r} not found for "
                f"tenant {tenant_id!r}"
            ),
        )

    connector = _repository_connector(repository)
    results: list[WorkflowResponse] = []
    errors: list[RepositoryIngestError] = []
    completed = 0
    dead_lettered = 0
    synchronized = False
    if request.sync_before_ingest:
        policy = SyncPolicy.from_settings(resources.settings.sync)
        sync_result = RepositorySynchronizer(db, connector, policy).synchronize(
            repository_id, tenant_id
        )
        cleaner = _vector_cleanup_service(resources)
        for event in sync_result.events:
            if event.event_type is not SyncEventType.DOCUMENT_DELETED:
                continue
            if event.document_id is None:
                continue
            try:
                cleaner.purge_document_vectors(event.document_id, tenant_id)
            except VectorCleanupError as exc:
                errors.append(
                    RepositoryIngestError(
                        document_id=event.document_id,
                        source_path=event.source_path or "",
                        message=f"vector cleanup failed: {exc}",
                    )
                )
        synchronized = True

    documents = _repository_documents(
        db,
        repository_id,
        tenant_id,
        document_ids=request.document_ids,
        max_documents=request.max_documents,
    )
    correlation_id = get_correlation_id()

    for document in documents:
        try:
            source_bytes = connector.read_bytes(document.source_path)
            result = orchestrator.run(
                document.id,
                tenant_id,
                source_bytes=source_bytes,
                correlation_id=correlation_id,
                intelligence_provider=intelligence_provider,
                intelligence_model=intelligence_model,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
            )
            results.append(_result_response(result))
            if result.status is WorkflowStatus.COMPLETED:
                completed += 1
            elif result.status is WorkflowStatus.DEAD_LETTER:
                dead_lettered += 1
        except (OSError, RuntimeError) as exc:
            errors.append(
                RepositoryIngestError(
                    document_id=document.id,
                    source_path=document.source_path,
                    message=str(exc),
                )
            )

    return RepositoryIngestResponse(
        repository_id=repository_id,
        tenant_id=tenant_id,
        synchronized=synchronized,
        attempted=len(documents),
        completed=completed,
        dead_lettered=dead_lettered,
        errors=errors,
        results=results,
    )

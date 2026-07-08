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
    JobKind,
    Repository,
)
from domain.jobs import SourceStore
from domain.observability import get_correlation_id, get_logger
from domain.orchestration import (
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowState,
    WorkflowStatus,
)
from domain.orchestration.state import StageRecord
from domain.publishing import (
    DocumentDeletionService,
    VectorCleanupError,
    VectorCleanupService,
    cleanup_provider_registry,
)
from domain.storage import compute_content_hash
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

logger = get_logger("ekie.api.ingestion")


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


class DocumentDeleteResponse(BaseModel):
    """Outcome of hard-deleting a document and its derived state."""

    document_id: str
    tenant_id: str
    vectors_deleted: int
    row_deleted: bool
    provider: str | None = None
    collection: str | None = None
    vector_cleanup_error: str | None = None
    message: str


class PurgeDocumentsRequest(BaseModel):
    """A DSAR/GDPR purge request naming the documents to hard-delete.

    EKIE data is scoped by tenant and document; it carries no user attribution, so
    the DSAR subscriber resolves the subject's document set upstream and supplies
    the identifiers here. The tenant is taken from the ``X-Tenant-ID`` header.
    """

    document_ids: list[str] = Field(min_length=1)
    reason: str = "dsar_purge"


class PurgeDocumentsResponse(BaseModel):
    """Outcome of a batch DSAR purge for a tenant."""

    tenant_id: str
    requested: int
    deleted_count: int
    vectors_deleted: int
    missing: list[str]
    reason: str


class JobAcceptedResponse(BaseModel):
    """Acknowledgement that an ingestion job was durably enqueued."""

    job_id: str
    document_id: str
    tenant_id: str
    kind: str
    status: str
    status_url: str
    message: str


class JobStatusResponse(BaseModel):
    """Current state of a durable ingestion job."""

    job_id: str
    document_id: str
    tenant_id: str
    kind: str
    status: str
    attempts: int
    max_attempts: int
    source_path: str | None = None
    last_error: str | None = None


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
    publishing = resources.settings.publishing
    return VectorCleanupService(
        resources.db,
        resources.storage,
        providers,
        fallback_provider=publishing.provider,
        fallback_collection=publishing.default_collection,
    )


def _document_deletion_service(resources: AppResources) -> DocumentDeletionService:
    """Build a document deletion service from active app resources."""
    return DocumentDeletionService(resources.db, _vector_cleanup_service(resources))


@router.post("/{document_id}/ingest", response_model=None)
async def ingest_document(
    document_id: str,
    request: Request,
    response: Response,
    tenant_id: TenantId,
    orchestrator: Orchestrator,
    resources: Resources,
    sync: bool = False,
    mime_type: str | None = None,
    intelligence_provider: str | None = None,
    intelligence_model: str | None = None,
    embedding_provider: str | None = None,
    embedding_model: str | None = None,
) -> WorkflowResponse | JobAcceptedResponse:
    """Ingest a synced document from raw bytes.

    When async ingestion is enabled (and ``sync`` is not requested) the source
    bytes are persisted, a durable job is enqueued, and the endpoint returns
    ``202 Accepted`` immediately so long pipelines never exhaust HTTP timeouts.
    Otherwise the full pipeline runs inline within the request.
    """
    source_bytes = await request.body()

    if resources.settings.ingestion.async_enabled and not sync:
        SourceStore(resources.db).store(tenant_id, document_id, source_bytes)
        job_id = resources.job_queue.enqueue(
            tenant_id=tenant_id,
            document_id=document_id,
            kind=JobKind.INGEST,
            content_hash=compute_content_hash(source_bytes),
            max_attempts=resources.settings.ingestion.max_attempts,
            correlation_id=get_correlation_id(),
            mime_type=mime_type,
            intelligence_provider=intelligence_provider,
            intelligence_model=intelligence_model,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        response.status_code = status.HTTP_202_ACCEPTED
        return JobAcceptedResponse(
            job_id=job_id,
            document_id=document_id,
            tenant_id=tenant_id,
            kind=JobKind.INGEST.value,
            status="queued",
            status_url=f"/v1/documents/{document_id}/job",
            message="ingestion job enqueued",
        )

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


@router.get("/{document_id}/job", response_model=JobStatusResponse)
async def document_job_status(
    document_id: str,
    tenant_id: TenantId,
    resources: Resources,
) -> JobStatusResponse:
    """Return the latest durable ingestion job for a document."""
    record = resources.job_queue.latest_for_document(document_id, tenant_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no ingestion job found for document {document_id!r}",
        )
    return JobStatusResponse(
        job_id=record.id,
        document_id=record.document_id,
        tenant_id=record.tenant_id,
        kind=record.kind.value,
        status=record.status.value,
        attempts=record.attempts,
        max_attempts=record.max_attempts,
        source_path=record.source_path,
        last_error=record.last_error,
    )


@router.post("/purge", response_model=PurgeDocumentsResponse)
async def purge_documents(
    request: PurgeDocumentsRequest,
    tenant_id: TenantId,
    resources: Resources,
) -> PurgeDocumentsResponse:
    """Hard-delete a set of documents for a tenant (DSAR/GDPR purge execution).

    Reuses the per-document deletion service with ``force=true`` so a vector-cleanup
    issue never leaves Control Plane rows behind. Documents not found for the tenant
    are reported in ``missing`` rather than failing the batch, keeping the purge
    idempotent. This is the surface a cross-engine purge subscriber invokes when it
    fans out an ``EnterpriseDataPurgeEvent``.
    """
    service = _document_deletion_service(resources)
    deleted = 0
    vectors_deleted = 0
    missing: list[str] = []
    for document_id in request.document_ids:
        result = service.delete_document(document_id, tenant_id, force=True)
        if result.row_deleted:
            deleted += 1
            vectors_deleted += result.vectors_deleted
        else:
            missing.append(document_id)
    logger.info(
        "documents_purged",
        extra={
            "tenant_id": tenant_id,
            "requested": len(request.document_ids),
            "deleted_count": deleted,
            "reason": request.reason,
            "correlation_id": get_correlation_id(),
        },
    )
    return PurgeDocumentsResponse(
        tenant_id=tenant_id,
        requested=len(request.document_ids),
        deleted_count=deleted,
        vectors_deleted=vectors_deleted,
        missing=missing,
        reason=request.reason,
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    tenant_id: TenantId,
    resources: Resources,
    force: bool = False,
) -> DocumentDeleteResponse:
    """Hard-delete a document: purge its vectors then remove Control Plane rows.

    Deleting the document row cascades to its assets, workflows, and processing
    state. With ``force=false`` (default) a vector-cleanup failure aborts the
    delete so it can be retried; ``force=true`` removes the row regardless.
    """
    service = _document_deletion_service(resources)
    try:
        result = service.delete_document(document_id, tenant_id, force=force)
    except VectorCleanupError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    if not result.row_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"document {document_id!r} not found for tenant {tenant_id!r}",
        )
    return DocumentDeleteResponse(
        document_id=result.document_id,
        tenant_id=result.tenant_id,
        vectors_deleted=result.vectors_deleted,
        row_deleted=result.row_deleted,
        provider=result.provider,
        collection=result.collection,
        vector_cleanup_error=result.vector_cleanup_error,
        message="document deleted",
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
        deleter = _document_deletion_service(resources)
        for event in sync_result.events:
            if event.event_type is not SyncEventType.DOCUMENT_DELETED:
                continue
            if event.document_id is None:
                continue
            deletion = deleter.delete_document(
                event.document_id, tenant_id, force=True
            )
            if deletion.vector_cleanup_error:
                errors.append(
                    RepositoryIngestError(
                        document_id=event.document_id,
                        source_path=event.source_path or "",
                        message=f"vector cleanup warning: {deletion.vector_cleanup_error}",
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

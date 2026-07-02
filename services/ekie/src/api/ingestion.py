"""Ingestion API: run and inspect document ingestion workflows.

Exposes the composition-root-built :class:`WorkflowOrchestrator` over REST. All
requests are tenant-scoped via the ``X-Tenant-ID`` header (bound by the
correlation middleware) and correlation-tagged via ``X-Correlation-ID``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from api.dependencies import (
    get_control_plane,
    get_orchestrator,
    require_tenant,
)
from domain.control_plane import ControlPlaneDatabase
from domain.observability import get_correlation_id
from domain.orchestration import (
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowState,
    WorkflowStatus,
)
from domain.orchestration.state import StageRecord

router = APIRouter(prefix="/v1/documents", tags=["ingestion"])

TenantId = Annotated[str, Depends(require_tenant)]
Orchestrator = Annotated[WorkflowOrchestrator, Depends(get_orchestrator)]
ControlPlane = Annotated[ControlPlaneDatabase, Depends(get_control_plane)]


class StageRecordResponse(BaseModel):
    """A completed stage in an ingestion workflow."""

    stage: str
    version: int
    created: bool
    content_hash: str
    attempts: int


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


def _records(records: tuple[StageRecord, ...]) -> list[StageRecordResponse]:
    """Map stage records into their response representation."""
    return [
        StageRecordResponse(
            stage=record.stage.value,
            version=record.version,
            created=record.created,
            content_hash=record.content_hash,
            attempts=record.attempts,
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


@router.post("/{document_id}/ingest", response_model=WorkflowResponse)
async def ingest_document(
    document_id: str,
    request: Request,
    response: Response,
    tenant_id: TenantId,
    orchestrator: Orchestrator,
    mime_type: str | None = None,
) -> WorkflowResponse:
    """Run the full ingestion workflow for a synced document from raw bytes."""
    source_bytes = await request.body()
    result = orchestrator.run(
        document_id,
        tenant_id,
        source_bytes=source_bytes,
        mime_type=mime_type,
        correlation_id=get_correlation_id(),
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
) -> WorkflowResponse:
    """Resume or replay a workflow from its checkpoint or Control Plane lineage."""
    body = await request.body()
    source_bytes = body if body else None
    result = orchestrator.resume(
        document_id,
        tenant_id,
        source_bytes=source_bytes,
        correlation_id=get_correlation_id(),
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

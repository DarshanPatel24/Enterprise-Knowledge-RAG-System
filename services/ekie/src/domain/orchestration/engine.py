"""Workflow orchestrator: drives the ingestion pipeline as a resumable graph.

The orchestrator threads an immutable :class:`WorkflowState` through the
transform -> intelligence -> chunk -> embed -> publish stages using a pluggable
runner (sequential by default, LangGraph when configured). It checkpoints after
every stage for resume, dead-letters on exhausted retries, and can reconcile a
workflow from Control Plane lineage for replay without a stored checkpoint
(handbook 6.20, EKIE-S7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from domain.control_plane import Asset, AssetType, ControlPlaneDatabase
from domain.observability import (
    correlation_scope,
    get_correlation_id,
    get_logger,
)
from domain.orchestration.checkpointer import Checkpointer, InMemoryCheckpointer
from domain.orchestration.events import OrchestrationEvent, OrchestrationEventType
from domain.orchestration.pipeline import PipelineEngines, Stage, default_stages
from domain.orchestration.policy import OrchestrationPolicy
from domain.orchestration.runner import WorkflowRunner, runner_from_policy
from domain.orchestration.state import (
    StageFailure,
    StageName,
    StageRecord,
    WorkflowState,
    WorkflowStatus,
)

logger = get_logger("ekie.orchestration")

_STAGE_ASSET_TYPE: dict[StageName, AssetType] = {
    StageName.TRANSFORM: AssetType.MARKDOWN,
    StageName.INTELLIGENCE: AssetType.INTELLIGENCE,
    StageName.CHUNK: AssetType.CHUNKS,
    StageName.EMBED: AssetType.EMBEDDING,
    StageName.PUBLISH: AssetType.VECTOR,
}


@dataclass(frozen=True)
class WorkflowResult:
    """Outcome of orchestrating a single document ingestion workflow."""

    document_id: str
    tenant_id: str
    correlation_id: str
    status: WorkflowStatus
    completed_stages: tuple[StageName, ...]
    records: tuple[StageRecord, ...]
    failure: StageFailure | None
    events: list[OrchestrationEvent] = field(default_factory=list)


class WorkflowOrchestrator:
    """Orchestrates the document ingestion pipeline with checkpoints and replay."""

    def __init__(
        self,
        db: ControlPlaneDatabase,
        engines: PipelineEngines,
        policy: OrchestrationPolicy,
        *,
        stages: tuple[Stage, ...] | None = None,
        checkpointer: Checkpointer | None = None,
        runner: WorkflowRunner | None = None,
        tracer_callbacks: list[object] | None = None,
    ) -> None:
        self._db = db
        self._engines = engines
        self._policy = policy
        self._stages = stages or default_stages()
        self._checkpointer = checkpointer or InMemoryCheckpointer()
        self._runner = runner or runner_from_policy(
            policy, tracer_callbacks=tracer_callbacks
        )

    def run(
        self,
        document_id: str,
        tenant_id: str,
        *,
        source_bytes: bytes,
        mime_type: str | None = None,
        correlation_id: str | None = None,
    ) -> WorkflowResult:
        """Run the full ingestion workflow for a freshly synced document."""
        cid = correlation_id or get_correlation_id() or str(uuid4())
        state = WorkflowState(
            document_id=document_id,
            tenant_id=tenant_id,
            correlation_id=cid,
            source_bytes=source_bytes,
            mime_type=mime_type,
        )
        return self._execute(state)

    def resume(
        self,
        document_id: str,
        tenant_id: str,
        *,
        source_bytes: bytes | None = None,
        correlation_id: str | None = None,
    ) -> WorkflowResult:
        """Resume or replay a workflow from its checkpoint or Control Plane lineage.

        Uses the stored checkpoint when present; otherwise reconstructs completed
        stages from Control Plane assets so already-materialized, idempotent
        stages are skipped on replay.
        """
        saved = self._checkpointer.load(tenant_id, document_id)
        if saved is None:
            saved = self.reconcile(document_id, tenant_id)
        cid = correlation_id or saved.correlation_id or get_correlation_id() or str(uuid4())
        state = saved.model_copy(
            update={
                "correlation_id": cid,
                "status": WorkflowStatus.RUNNING,
                "failure": None,
                "source_bytes": source_bytes
                if source_bytes is not None
                else saved.source_bytes,
            }
        )
        return self._execute(state)

    def reconcile(self, document_id: str, tenant_id: str) -> WorkflowState:
        """Reconstruct workflow state from Control Plane lineage for replay.

        Walks the stages in order and marks each complete while its output asset
        exists, stopping at the first gap so completed stages form a contiguous
        prefix that the runner can safely skip.
        """
        records: list[StageRecord] = []
        with self._db.session() as session:
            for stage in self._stages:
                asset_type = _STAGE_ASSET_TYPE[stage.name]
                asset = (
                    session.query(Asset)
                    .filter(
                        Asset.document_id == document_id,
                        Asset.tenant_id == tenant_id,
                        Asset.asset_type == asset_type,
                    )
                    .order_by(Asset.version.desc())
                    .first()
                )
                if asset is None:
                    break
                records.append(
                    StageRecord(
                        stage=stage.name,
                        asset_id=asset.id,
                        version=asset.version,
                        content_hash=asset.content_hash,
                        created=False,
                    )
                )
        completed = tuple(record.stage for record in records)
        if len(completed) == len(self._stages):
            status = WorkflowStatus.COMPLETED
        elif completed:
            status = WorkflowStatus.RUNNING
        else:
            status = WorkflowStatus.PENDING
        return WorkflowState(
            document_id=document_id,
            tenant_id=tenant_id,
            correlation_id=get_correlation_id() or str(uuid4()),
            status=status,
            completed_stages=completed,
            records=tuple(records),
        )

    def checkpoint(self, tenant_id: str, document_id: str) -> WorkflowState | None:
        """Return the stored checkpoint for a workflow, if any."""
        return self._checkpointer.load(tenant_id, document_id)

    def _execute(self, state: WorkflowState) -> WorkflowResult:
        """Run the configured runner within a bound correlation scope."""
        events: list[OrchestrationEvent] = []

        def emit(
            event_type: OrchestrationEventType,
            stage: StageName | None = None,
            detail: str = "",
        ) -> None:
            events.append(
                OrchestrationEvent(
                    event_type=event_type,
                    document_id=state.document_id,
                    tenant_id=state.tenant_id,
                    correlation_id=state.correlation_id,
                    stage=stage,
                    detail=detail,
                )
            )

        with correlation_scope(
            tenant_id=state.tenant_id, correlation_id=state.correlation_id
        ):
            logger.info(
                "workflow_started",
                extra={"document_id": state.document_id, "runner": self._policy.runner},
            )
            emit(OrchestrationEventType.WORKFLOW_STARTED)
            final = self._runner.run(
                state=state,
                engines=self._engines,
                stages=self._stages,
                policy=self._policy,
                checkpointer=self._checkpointer,
                emit=emit,
            )
            logger.info(
                "workflow_finished",
                extra={
                    "document_id": state.document_id,
                    "status": final.status.value,
                    "completed_stages": [s.value for s in final.completed_stages],
                },
            )

        return WorkflowResult(
            document_id=final.document_id,
            tenant_id=final.tenant_id,
            correlation_id=final.correlation_id,
            status=final.status,
            completed_stages=final.completed_stages,
            records=final.records,
            failure=final.failure,
            events=events,
        )

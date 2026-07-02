"""Typed workflow state for the ingestion orchestration graph (handbook 6.20).

The state is an immutable Pydantic model threaded through pure-function stage
nodes. Every transition returns a new state via ``model_copy`` so the graph
remains deterministic and the LangGraph checkpointer can persist snapshots for
resume, dead-letter recovery, and lineage-aware replay.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class StageName(StrEnum):
    """Ordered ingestion stages driven by the orchestrator."""

    TRANSFORM = "transform"
    INTELLIGENCE = "intelligence"
    CHUNK = "chunk"
    EMBED = "embed"
    PUBLISH = "publish"


class WorkflowStatus(StrEnum):
    """Terminal and transient states of a document ingestion workflow."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    DEAD_LETTER = "dead_letter"


class StageRecord(BaseModel):
    """Immutable record of a successfully completed stage."""

    model_config = {"frozen": True}

    stage: StageName
    asset_id: str
    version: int
    content_hash: str
    created: bool
    attempts: int = 1


class StageFailure(BaseModel):
    """Immutable record of the failure that dead-lettered a workflow."""

    model_config = {"frozen": True}

    stage: StageName
    error_type: str
    message: str
    attempts: int


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class WorkflowState(BaseModel):
    """Immutable, checkpointable state of a single document ingestion workflow."""

    model_config = {"frozen": True}

    document_id: str
    tenant_id: str
    correlation_id: str
    source_bytes: bytes | None = None
    mime_type: str | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    completed_stages: tuple[StageName, ...] = ()
    records: tuple[StageRecord, ...] = ()
    failure: StageFailure | None = None
    updated_at: datetime = Field(default_factory=_utc_now)

    def is_complete(self, stage: StageName) -> bool:
        """Return whether ``stage`` already completed in this workflow."""
        return stage in self.completed_stages

    def with_record(self, record: StageRecord) -> WorkflowState:
        """Return a new state that appends a completed-stage record."""
        return self.model_copy(
            update={
                "completed_stages": (*self.completed_stages, record.stage),
                "records": (*self.records, record),
                "status": WorkflowStatus.RUNNING,
                "failure": None,
                "updated_at": _utc_now(),
            }
        )

    def marked(
        self, status: WorkflowStatus, *, failure: StageFailure | None = None
    ) -> WorkflowState:
        """Return a new state with an updated status and optional failure."""
        return self.model_copy(
            update={"status": status, "failure": failure, "updated_at": _utc_now()}
        )

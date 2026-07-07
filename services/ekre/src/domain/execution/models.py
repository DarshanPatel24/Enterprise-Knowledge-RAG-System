"""Execution domain models: tasks, worker outcomes, and execution sessions.

The execution core consumes a :class:`RetrievalPlan` (from the query intelligence
domain) and produces a standardized, deterministic candidate collection. All
models are immutable so execution results are reproducible and auditable.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from contracts.retrieval import RetrievalCandidate
from domain.query.models import MetadataFilter, RetrievalEngineType


class WorkerState(StrEnum):
    """Standard retrieval worker lifecycle states (handbook Chapter 18.6)."""

    CREATED = "created"
    INITIALIZED = "initialized"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    DEGRADED = "degraded"


class ExecutionStatus(StrEnum):
    """Overall status of an execution session."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class WorkerDescriptor(BaseModel):
    """Capability advertisement a worker registers with the framework."""

    model_config = ConfigDict(frozen=True)

    worker_id: str = Field(min_length=1)
    engine: RetrievalEngineType
    version: str = "1.0.0"
    supported_task_types: tuple[str, ...] = ()


class RetrievalTask(BaseModel):
    """A single executable retrieval task derived from a plan step."""

    model_config = ConfigDict(frozen=True)

    task_id: str = Field(min_length=1)
    engine: RetrievalEngineType
    query: str
    candidate_limit: int = Field(gt=0)
    timeout_ms: float = Field(gt=0.0)
    parallel_group: int = Field(ge=0)
    # Empty tenant is representable so admission control can reject it.
    tenant_id: str = ""
    metadata_filters: tuple[MetadataFilter, ...] = ()
    priority: int = 0


class WorkerOutcome(BaseModel):
    """The standardized result of executing one task on one worker."""

    model_config = ConfigDict(frozen=True)

    task_id: str
    worker_id: str
    engine: RetrievalEngineType
    state: WorkerState
    candidates: tuple[RetrievalCandidate, ...] = ()
    error_type: str | None = None
    message: str | None = None
    duration_ms: float = 0.0
    attempts: int = 1
    transitions: tuple[WorkerState, ...] = ()

    @property
    def succeeded(self) -> bool:
        """Return whether the task completed successfully."""
        return self.state is WorkerState.COMPLETED


class ExecutionSession(BaseModel):
    """The immutable result of executing a retrieval plan."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    correlation_id: str | None = None
    status: ExecutionStatus
    degraded: bool = False
    outcomes: tuple[WorkerOutcome, ...] = ()
    candidates: tuple[RetrievalCandidate, ...] = ()
    worker_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    candidate_count: int = 0
    duration_ms: float = 0.0

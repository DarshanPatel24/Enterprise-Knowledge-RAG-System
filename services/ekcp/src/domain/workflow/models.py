"""Workflow models and lifecycle (handbook Chapter 15).

A workflow is a governed, long-running business process (distinct from a static
plan): it carries a state, an execution plan reference, milestones, and an audit
trail. Workflows are immutable; transitions produce a new workflow via
``model_copy``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class WorkflowState(StrEnum):
    """Workflow lifecycle states (handbook 15)."""

    CREATED = "created"
    PLANNED = "planned"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"
    PAUSED = "paused"
    REPLANNED = "replanned"


class WorkflowTransition(BaseModel):
    """Immutable record of a workflow state change."""

    model_config = ConfigDict(frozen=True)

    from_state: WorkflowState
    to_state: WorkflowState
    reason: str
    timestamp: datetime = Field(default_factory=_utc_now)


class Workflow(BaseModel):
    """Immutable governed, long-running workflow."""

    model_config = ConfigDict(frozen=True)

    workflow_id: str
    tenant_id: str
    objective: str
    state: WorkflowState = WorkflowState.CREATED
    plan_id: str | None = None
    task_count: int = 0
    milestones: tuple[str, ...] = ()
    transitions: tuple[WorkflowTransition, ...] = ()
    correlation_id: str | None = None
    version_number: int = 0
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

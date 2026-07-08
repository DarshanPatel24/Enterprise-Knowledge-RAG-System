"""Workflow lifecycle state machine (handbook Chapter 15)."""

from __future__ import annotations

from datetime import UTC, datetime

from domain.workflow.errors import WorkflowError, WorkflowErrorType
from domain.workflow.models import Workflow, WorkflowState, WorkflowTransition

_ALLOWED_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.CREATED: frozenset({WorkflowState.PLANNED, WorkflowState.FAILED}),
    WorkflowState.PLANNED: frozenset(
        {WorkflowState.EXECUTING, WorkflowState.PAUSED, WorkflowState.FAILED}
    ),
    WorkflowState.EXECUTING: frozenset(
        {
            WorkflowState.WAITING,
            WorkflowState.PAUSED,
            WorkflowState.COMPLETED,
            WorkflowState.REPLANNED,
            WorkflowState.FAILED,
        }
    ),
    WorkflowState.WAITING: frozenset(
        {WorkflowState.EXECUTING, WorkflowState.COMPLETED, WorkflowState.FAILED}
    ),
    WorkflowState.PAUSED: frozenset(
        {WorkflowState.EXECUTING, WorkflowState.COMPLETED, WorkflowState.FAILED}
    ),
    WorkflowState.REPLANNED: frozenset(
        {WorkflowState.EXECUTING, WorkflowState.FAILED}
    ),
    WorkflowState.COMPLETED: frozenset({WorkflowState.ARCHIVED}),
    WorkflowState.ARCHIVED: frozenset(),
    WorkflowState.FAILED: frozenset(),
}


def is_allowed(from_state: WorkflowState, to_state: WorkflowState) -> bool:
    """Return whether ``from_state`` may legally transition to ``to_state``."""
    return to_state in _ALLOWED_TRANSITIONS.get(from_state, frozenset())


def transition(
    workflow: Workflow,
    to_state: WorkflowState,
    *,
    reason: str,
    now: datetime | None = None,
) -> Workflow:
    """Return a new workflow transitioned to ``to_state`` with history and version bump."""
    if not is_allowed(workflow.state, to_state):
        raise WorkflowError(
            WorkflowErrorType.INVALID_TRANSITION,
            f"illegal workflow transition {workflow.state} -> {to_state}",
        )
    timestamp = now or datetime.now(UTC)
    record = WorkflowTransition(
        from_state=workflow.state,
        to_state=to_state,
        reason=reason,
        timestamp=timestamp,
    )
    return workflow.model_copy(
        update={
            "state": to_state,
            "transitions": (*workflow.transitions, record),
            "version_number": workflow.version_number + 1,
            "updated_at": timestamp,
        }
    )

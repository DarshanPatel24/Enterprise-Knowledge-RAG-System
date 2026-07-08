"""Tests for the workflow orchestrator, lifecycle, and event bus."""

from __future__ import annotations

import pytest

from config.settings import PlanningSettings, WorkflowSettings
from domain.planning import PlanningEngine, PlanningPolicy
from domain.workflow import (
    InMemoryEventBus,
    InMemoryWorkflowStore,
    PlatformEventType,
    Workflow,
    WorkflowError,
    WorkflowOrchestrator,
    WorkflowState,
    is_allowed,
    transition,
)


def _orchestrator() -> tuple[WorkflowOrchestrator, InMemoryEventBus]:
    planner = PlanningEngine(PlanningPolicy.from_settings(PlanningSettings(_env_file=None)))
    bus = InMemoryEventBus()
    _ = WorkflowSettings(_env_file=None)
    orchestrator = WorkflowOrchestrator(InMemoryWorkflowStore(), planner, bus)
    return orchestrator, bus


def _workflow(state: WorkflowState = WorkflowState.CREATED) -> Workflow:
    return Workflow(
        workflow_id="wf-1", tenant_id="tenant-a", objective="do it", state=state
    )


def test_lifecycle_transitions() -> None:
    assert is_allowed(WorkflowState.CREATED, WorkflowState.PLANNED)
    assert is_allowed(WorkflowState.EXECUTING, WorkflowState.COMPLETED)
    assert not is_allowed(WorkflowState.COMPLETED, WorkflowState.EXECUTING)
    assert not is_allowed(WorkflowState.ARCHIVED, WorkflowState.PLANNED)


def test_transition_records_history() -> None:
    planned = transition(_workflow(), WorkflowState.PLANNED, reason="decomposed")
    assert planned.state is WorkflowState.PLANNED
    assert planned.version_number == 1
    assert planned.transitions[-1].to_state is WorkflowState.PLANNED


def test_illegal_transition_raises() -> None:
    with pytest.raises(WorkflowError):
        transition(_workflow(WorkflowState.ARCHIVED), WorkflowState.PLANNED, reason="x")


def test_trigger_creates_planned_workflow_with_events() -> None:
    orchestrator, bus = _orchestrator()
    workflow = orchestrator.trigger(
        tenant_id="tenant-a",
        objective="retrieve sales data, generate report, notify stakeholders",
    )
    assert workflow.state is WorkflowState.PLANNED
    assert workflow.plan_id is not None
    assert workflow.task_count >= 2
    event_types = [event.event_type for event in bus.history()]
    assert PlatformEventType.WORKFLOW_TRIGGERED in event_types
    assert PlatformEventType.WORKFLOW_PLANNED in event_types


def test_pause_resume_flow() -> None:
    orchestrator, _ = _orchestrator()
    workflow = orchestrator.trigger(tenant_id="tenant-a", objective="do the thing")
    paused = orchestrator.pause("tenant-a", workflow.workflow_id)
    assert paused.state is WorkflowState.PAUSED
    resumed = orchestrator.resume("tenant-a", workflow.workflow_id)
    assert resumed.state is WorkflowState.EXECUTING


def test_approve_requires_waiting_or_paused() -> None:
    orchestrator, _ = _orchestrator()
    workflow = orchestrator.trigger(tenant_id="tenant-a", objective="do the thing")
    # PLANNED state cannot be approved directly.
    with pytest.raises(WorkflowError):
        orchestrator.approve("tenant-a", workflow.workflow_id)
    orchestrator.pause("tenant-a", workflow.workflow_id)
    approved = orchestrator.approve("tenant-a", workflow.workflow_id)
    assert approved.state is WorkflowState.EXECUTING


def test_get_missing_workflow_raises() -> None:
    orchestrator, _ = _orchestrator()
    with pytest.raises(WorkflowError):
        orchestrator.get("tenant-a", "wf-missing")

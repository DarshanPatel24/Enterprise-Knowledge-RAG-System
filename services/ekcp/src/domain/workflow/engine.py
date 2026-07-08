"""Workflow orchestrator: trigger, pause, resume, complete, approve.

Triggers a governed workflow by decomposing the objective into an execution plan
(reusing the S5 planning engine), then advancing it through its lifecycle while
publishing platform events for full traceability. Orchestration is deterministic;
a full distributed workflow engine is a later concern.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from domain.observability import get_correlation_id, get_logger
from domain.planning import PlanningEngine
from domain.workflow.errors import WorkflowError, WorkflowErrorType
from domain.workflow.events import (
    EventBus,
    PlatformEventType,
    build_platform_event,
)
from domain.workflow.lifecycle import transition
from domain.workflow.models import Workflow, WorkflowState
from domain.workflow.store import WorkflowStore

logger = get_logger("ekcp.workflow.engine")

_ACTIVE_STATES = frozenset(
    {WorkflowState.PLANNED, WorkflowState.EXECUTING, WorkflowState.WAITING}
)


class WorkflowOrchestrator:
    """Orchestrate governed, long-running workflows with event traceability."""

    def __init__(
        self,
        store: WorkflowStore,
        planner: PlanningEngine,
        event_bus: EventBus,
        *,
        source_service: str = "ekcp",
        enable_events: bool = True,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._planner = planner
        self._bus = event_bus
        self._source = source_service
        self._enable_events = enable_events
        self._clock = clock or (lambda: datetime.now(UTC))

    def trigger(self, *, tenant_id: str, objective: str) -> Workflow:
        """Create a workflow and generate its execution plan (CREATED -> PLANNED)."""
        now = self._clock()
        workflow = Workflow(
            workflow_id=f"wf-{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            objective=objective,
            correlation_id=get_correlation_id(),
            created_at=now,
            updated_at=now,
        )
        self._store.save(workflow)
        self._emit(PlatformEventType.WORKFLOW_TRIGGERED, workflow)

        plan = self._planner.plan(objective)
        planned = transition(
            workflow, WorkflowState.PLANNED, reason="objective decomposed", now=now
        ).model_copy(update={"plan_id": plan.plan_id, "task_count": len(plan.tasks)})
        self._store.save(planned)
        self._emit(
            PlatformEventType.WORKFLOW_PLANNED,
            planned,
            payload={"plan_id": plan.plan_id, "task_count": str(len(plan.tasks))},
        )
        logger.info(
            "workflow_triggered",
            extra={"workflow_id": planned.workflow_id, "task_count": len(plan.tasks)},
        )
        return planned

    def get(self, tenant_id: str, workflow_id: str) -> Workflow:
        """Return the current workflow."""
        return self._store.get(tenant_id, workflow_id)

    def pause(self, tenant_id: str, workflow_id: str) -> Workflow:
        """Pause an active workflow and checkpoint it."""
        workflow = self._store.get(tenant_id, workflow_id)
        paused = transition(workflow, WorkflowState.PAUSED, reason="user paused")
        self._store.save(paused)
        self._emit(PlatformEventType.WORKFLOW_PAUSED, paused)
        return paused

    def resume(self, tenant_id: str, workflow_id: str) -> Workflow:
        """Resume a paused workflow from its checkpoint."""
        workflow = self._store.get(tenant_id, workflow_id)
        resumed = transition(workflow, WorkflowState.EXECUTING, reason="user resumed")
        self._store.save(resumed)
        self._emit(PlatformEventType.WORKFLOW_RESUMED, resumed)
        return resumed

    def approve(self, tenant_id: str, workflow_id: str) -> Workflow:
        """Record a human approval, advancing a waiting workflow to executing."""
        workflow = self._store.get(tenant_id, workflow_id)
        if workflow.state not in (WorkflowState.WAITING, WorkflowState.PAUSED):
            raise WorkflowError(
                WorkflowErrorType.INVALID_STATE,
                f"workflow {workflow_id} is {workflow.state} and cannot be approved",
            )
        self._emit(PlatformEventType.APPROVAL_RECEIVED, workflow)
        approved = transition(
            workflow, WorkflowState.EXECUTING, reason="approval received"
        )
        self._store.save(approved)
        return approved

    def _emit(
        self,
        event_type: PlatformEventType,
        workflow: Workflow,
        *,
        payload: dict[str, str] | None = None,
    ) -> None:
        if not self._enable_events:
            return
        detail = {"workflow_id": workflow.workflow_id, "state": workflow.state}
        if payload:
            detail.update(payload)
        self._bus.publish(
            build_platform_event(
                event_type,
                tenant_id=workflow.tenant_id,
                source_service=self._source,
                payload=detail,
            )
        )

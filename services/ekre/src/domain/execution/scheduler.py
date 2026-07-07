"""Execution scheduler (handbook Chapter 17).

Turns a :class:`RetrievalPlan` into admitted, prioritized :class:`RetrievalTask`
instances. Admission control validates each step before it enters execution;
priority is computed (never hardcoded) so ordering is deterministic. The
scheduler decides *when and where* tasks run; it never executes retrieval.
"""

from __future__ import annotations

from domain.execution.models import RetrievalTask
from domain.execution.policy import ExecutionPolicy
from domain.query.models import (
    MetadataFilter,
    RetrievalEngineType,
    RetrievalPlan,
    RetrievalStep,
)

# Deterministic engine priority (lower value schedules first) when steps share a
# parallel group. Vector is the primary signal, then keyword, then metadata.
_ENGINE_PRIORITY: dict[RetrievalEngineType, int] = {
    RetrievalEngineType.VECTOR: 0,
    RetrievalEngineType.KEYWORD: 1,
    RetrievalEngineType.METADATA: 2,
}


class ExecutionScheduler:
    """Admission control and deterministic task prioritization."""

    def __init__(self, policy: ExecutionPolicy) -> None:
        self._policy = policy

    def schedule(
        self,
        plan: RetrievalPlan,
        *,
        tenant_id: str,
        query: str = "",
        metadata_filters: tuple[MetadataFilter, ...] = (),
    ) -> list[RetrievalTask]:
        """Return admitted, deterministically ordered tasks for the plan."""
        admitted: list[RetrievalTask] = []
        for step in plan.steps:
            task = self._build_task(plan, step, tenant_id, query, metadata_filters)
            if self._admit(task):
                admitted.append(task)
        admitted.sort(key=lambda task: (task.parallel_group, task.priority, task.engine.value))
        return admitted

    def _build_task(
        self,
        plan: RetrievalPlan,
        step: RetrievalStep,
        tenant_id: str,
        query: str,
        metadata_filters: tuple[MetadataFilter, ...],
    ) -> RetrievalTask:
        timeout = step.timeout_ms or self._policy.default_task_timeout_ms
        return RetrievalTask(
            task_id=f"{plan.plan_id}-{step.engine.value}",
            engine=step.engine,
            query=query,
            candidate_limit=step.candidate_limit,
            timeout_ms=timeout,
            parallel_group=step.parallel_group,
            tenant_id=tenant_id,
            metadata_filters=metadata_filters,
            priority=_ENGINE_PRIORITY.get(step.engine, 99),
        )

    def _admit(self, task: RetrievalTask) -> bool:
        """Validate a task before it enters execution (admission control)."""
        if not self._policy.admission_enabled:
            return True
        if not task.tenant_id:
            return False
        if task.timeout_ms <= 0.0:
            return False
        return task.candidate_limit > 0

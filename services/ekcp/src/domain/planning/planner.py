"""Planning engine: deterministic intent decomposition (handbook 11.4).

Transforms a user objective into an ordered task plan using a rule-based
decomposition: recognized objective signals expand into capability-scoped tasks
with finish-to-start dependencies and human approval gates. Decomposition is
deterministic and bounded by the plan-size policy. Model-assisted planning is a
later enhancement; the deterministic path keeps planning reproducible offline.
"""

from __future__ import annotations

import uuid

from domain.observability import get_logger
from domain.planning.errors import PlanningError, PlanningErrorType
from domain.planning.models import (
    ApprovalCheckpoint,
    ExecutionPlan,
    ExecutionStrategy,
    Task,
)
from domain.planning.policy import PlanningPolicy

logger = get_logger("ekcp.planning")

# Ordered decomposition rules: a matched signal contributes a task template.
# Each template is (signal keywords, description, capability, approval_required).
_RULES: tuple[tuple[tuple[str, ...], str, str, bool], ...] = (
    (
        ("retrieve", "fetch", "gather", "sales", "data"),
        "Retrieve required data",
        "sql_querying",
        False,
    ),
    (("validate", "check", "completeness"), "Validate data completeness", "data_analysis", False),
    (("report", "summary", "summarize"), "Generate the report", "reporting", False),
    (("compliance", "policy", "regulation"), "Perform compliance review", "validation", False),
    (
        ("approve", "approval", "sign-off", "signoff"),
        "Obtain manager approval",
        "reasoning",
        True,
    ),
    (
        ("notify", "inform", "email", "stakeholder"),
        "Notify stakeholders",
        "workflow_execution",
        False,
    ),
    (("analyze", "compare", "trend"), "Analyze the results", "data_analysis", False),
)


class PlanningEngine:
    """Decompose an objective into an ordered, dependency-aware execution plan."""

    def __init__(self, policy: PlanningPolicy) -> None:
        self._policy = policy

    def plan(self, objective: str) -> ExecutionPlan:
        """Return an execution plan for the objective."""
        text = objective.strip()
        if not text:
            raise PlanningError(
                PlanningErrorType.EMPTY_OBJECTIVE, "objective must not be empty"
            )
        lowered = text.lower()

        specs: list[tuple[str, str, bool]] = []
        for keywords, description, capability, approval in _RULES:
            if any(keyword in lowered for keyword in keywords):
                specs.append((description, capability, approval))
        if not specs:
            specs.append(("Fulfill the request", "reasoning", False))

        specs = specs[: self._policy.max_tasks]
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
        tasks: list[Task] = []
        checkpoints: list[ApprovalCheckpoint] = []
        previous_id: str | None = None
        for index, (description, capability, approval) in enumerate(specs, start=1):
            task_id = f"{plan_id}-t{index}"
            tasks.append(
                Task(
                    task_id=task_id,
                    description=description,
                    required_capability=capability,
                    dependencies=(previous_id,) if previous_id else (),
                    priority=index,
                    approval_required=approval,
                    timeout_seconds=self._policy.default_task_timeout_seconds,
                )
            )
            if approval:
                checkpoints.append(
                    ApprovalCheckpoint(
                        checkpoint_id=f"{task_id}-approval", task_id=task_id
                    )
                )
            previous_id = task_id

        strategy = (
            ExecutionStrategy.CONDITIONAL if checkpoints else ExecutionStrategy.SEQUENTIAL
        )
        plan = ExecutionPlan(
            plan_id=plan_id,
            objective=text,
            tasks=tuple(tasks),
            execution_strategy=strategy,
            approval_checkpoints=tuple(checkpoints),
        )
        logger.info(
            "plan_created",
            extra={"plan_id": plan_id, "task_count": len(tasks)},
        )
        return plan

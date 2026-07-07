"""Tests for the planning engine and dependency graph."""

from __future__ import annotations

import pytest

from config.settings import PlanningSettings
from domain.planning import (
    ExecutionStrategy,
    PlanningEngine,
    PlanningError,
    PlanningPolicy,
    Task,
    topological_order,
)


def _engine(**overrides: object) -> PlanningEngine:
    settings = PlanningSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return PlanningEngine(PlanningPolicy.from_settings(settings))


def test_quarterly_report_decomposition() -> None:
    plan = _engine().plan(
        "Retrieve sales data, generate the report, compliance review, "
        "obtain approval, and notify stakeholders"
    )
    capabilities = [task.required_capability for task in plan.tasks]
    assert "sql_querying" in capabilities
    assert "reporting" in capabilities
    assert "validation" in capabilities
    assert "workflow_execution" in capabilities
    assert plan.execution_strategy is ExecutionStrategy.CONDITIONAL
    assert any(task.approval_required for task in plan.tasks)
    assert plan.approval_checkpoints


def test_dependencies_are_finish_to_start_chain() -> None:
    plan = _engine().plan("retrieve data and generate report")
    assert plan.tasks[0].dependencies == ()
    assert plan.tasks[1].dependencies == (plan.tasks[0].task_id,)


def test_generic_objective_single_task() -> None:
    plan = _engine().plan("tell me something interesting")
    assert len(plan.tasks) == 1
    assert plan.tasks[0].required_capability == "reasoning"
    assert plan.execution_strategy is ExecutionStrategy.SEQUENTIAL


def test_empty_objective_raises() -> None:
    with pytest.raises(PlanningError):
        _engine().plan("   ")


def test_max_tasks_cap() -> None:
    plan = _engine(max_tasks=2).plan(
        "retrieve data, validate, generate report, compliance, notify"
    )
    assert len(plan.tasks) == 2


def test_topological_order_and_cycle_detection() -> None:
    tasks = (
        Task(task_id="t1", description="a", required_capability="reasoning"),
        Task(
            task_id="t2",
            description="b",
            required_capability="reasoning",
            dependencies=("t1",),
        ),
    )
    ordered = topological_order(tasks)
    assert [t.task_id for t in ordered] == ["t1", "t2"]

    cyclic = (
        Task(
            task_id="a",
            description="a",
            required_capability="reasoning",
            dependencies=("b",),
        ),
        Task(
            task_id="b",
            description="b",
            required_capability="reasoning",
            dependencies=("a",),
        ),
    )
    with pytest.raises(PlanningError):
        topological_order(cyclic)

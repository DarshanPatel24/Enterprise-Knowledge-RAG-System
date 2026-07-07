"""Tests for the execution scheduler (admission + deterministic ordering)."""

from __future__ import annotations

from _execution_support import plan

from domain.execution import ExecutionPolicy, ExecutionScheduler
from domain.query.models import RetrievalEngineType


def _scheduler(*, admission: bool = True) -> ExecutionScheduler:
    policy = ExecutionPolicy(admission_enabled=admission)
    return ExecutionScheduler(policy)


def test_schedule_builds_task_per_step() -> None:
    tasks = _scheduler().schedule(
        plan(RetrievalEngineType.VECTOR, RetrievalEngineType.KEYWORD),
        tenant_id="tenant-a",
        query="hello",
    )
    assert {t.engine for t in tasks} == {
        RetrievalEngineType.VECTOR,
        RetrievalEngineType.KEYWORD,
    }
    assert all(t.query == "hello" for t in tasks)
    assert all(t.tenant_id == "tenant-a" for t in tasks)


def test_deterministic_priority_order() -> None:
    tasks = _scheduler().schedule(
        plan(RetrievalEngineType.METADATA, RetrievalEngineType.VECTOR),
        tenant_id="tenant-a",
    )
    # Vector (priority 0) is scheduled before metadata (priority 2).
    assert tasks[0].engine is RetrievalEngineType.VECTOR


def test_admission_rejects_when_tenant_missing() -> None:
    tasks = _scheduler().schedule(plan(RetrievalEngineType.VECTOR), tenant_id="")
    assert tasks == []


def test_admission_disabled_admits_all() -> None:
    tasks = _scheduler(admission=False).schedule(
        plan(RetrievalEngineType.VECTOR), tenant_id=""
    )
    assert len(tasks) == 1

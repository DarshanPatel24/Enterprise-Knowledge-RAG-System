"""Tests for the execution runners (parallel, deterministic, timeout, retry)."""

from __future__ import annotations

import importlib.util

import pytest
from _execution_support import SlowWorker, candidate, plan, static_worker

from domain.execution import (
    ConcurrentExecutionRunner,
    ExecutionPolicy,
    ExecutionScheduler,
    LangGraphExecutionRunner,
    WorkerRegistry,
    WorkerState,
)
from domain.query.models import RetrievalEngineType


def _tasks(*engines: RetrievalEngineType, timeout_ms: float = 150.0) -> list:
    scheduler = ExecutionScheduler(ExecutionPolicy())
    return scheduler.schedule(plan(*engines, timeout_ms=timeout_ms), tenant_id="tenant-a")


def _registry() -> WorkerRegistry:
    registry = WorkerRegistry()
    registry.register(static_worker(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]))
    registry.register(static_worker(RetrievalEngineType.KEYWORD, [candidate("d2", "c2", 0.8)]))
    return registry


def test_concurrent_runner_returns_outcomes_in_task_order() -> None:
    tasks = _tasks(RetrievalEngineType.VECTOR, RetrievalEngineType.KEYWORD)
    outcomes = ConcurrentExecutionRunner().run(
        tasks, _registry(), security_context=None, max_attempts=1
    )
    assert [o.task_id for o in outcomes] == [t.task_id for t in tasks]
    assert all(o.state is WorkerState.COMPLETED for o in outcomes)


def test_missing_worker_is_isolated() -> None:
    tasks = _tasks(RetrievalEngineType.METADATA)
    outcomes = ConcurrentExecutionRunner().run(
        tasks, _registry(), security_context=None, max_attempts=1
    )
    assert outcomes[0].state is WorkerState.FAILED
    assert outcomes[0].error_type == "unknown_worker"


def test_slow_worker_times_out() -> None:
    registry = WorkerRegistry()
    registry.register(SlowWorker(RetrievalEngineType.VECTOR, delay_seconds=0.2))
    tasks = _tasks(RetrievalEngineType.VECTOR, timeout_ms=5.0)
    outcomes = ConcurrentExecutionRunner().run(
        tasks, registry, security_context=None, max_attempts=1
    )
    assert outcomes[0].state is WorkerState.TIMED_OUT


@pytest.mark.skipif(
    importlib.util.find_spec("langgraph") is None, reason="langgraph not installed"
)
def test_langgraph_runner_matches_concurrent() -> None:
    tasks = _tasks(RetrievalEngineType.VECTOR, RetrievalEngineType.KEYWORD)
    outcomes = LangGraphExecutionRunner().run(
        tasks, _registry(), security_context=None, max_attempts=1
    )
    assert [o.task_id for o in outcomes] == [t.task_id for t in tasks]
    assert all(o.state is WorkerState.COMPLETED for o in outcomes)

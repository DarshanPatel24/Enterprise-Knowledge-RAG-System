"""Tests for worker lifecycle execution and failure isolation."""

from __future__ import annotations

from _execution_support import FailingWorker, candidate, static_worker

from domain.execution import RetrievalTask, WorkerState, run_worker
from domain.query.models import RetrievalEngineType


def _task(*, candidate_limit: int = 5) -> RetrievalTask:
    return RetrievalTask(
        task_id="t1",
        engine=RetrievalEngineType.VECTOR,
        query="q",
        candidate_limit=candidate_limit,
        timeout_ms=150.0,
        parallel_group=0,
        tenant_id="tenant-a",
    )


def test_successful_worker_completes_with_transitions() -> None:
    worker = static_worker(
        RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]
    )
    outcome = run_worker(worker, _task(), security_context=None)
    assert outcome.state is WorkerState.COMPLETED
    assert outcome.succeeded
    assert outcome.transitions[0] is WorkerState.CREATED
    assert outcome.transitions[-1] is WorkerState.COMPLETED
    assert len(outcome.candidates) == 1


def test_candidates_clamped_to_limit() -> None:
    worker = static_worker(
        RetrievalEngineType.VECTOR,
        [candidate("d1", "c1", 0.9), candidate("d2", "c2", 0.8)],
    )
    outcome = run_worker(worker, _task(candidate_limit=1), security_context=None)
    assert len(outcome.candidates) == 1


def test_failing_worker_is_isolated() -> None:
    outcome = run_worker(
        FailingWorker(RetrievalEngineType.VECTOR), _task(), security_context=None
    )
    assert outcome.state is WorkerState.FAILED
    assert outcome.error_type == "worker_failure"
    assert not outcome.succeeded

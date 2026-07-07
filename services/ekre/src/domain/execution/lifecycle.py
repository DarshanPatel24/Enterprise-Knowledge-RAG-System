"""Worker lifecycle execution and failure isolation (handbook Chapter 18.6).

Wraps a single worker call in the standard lifecycle, records state transitions,
times the execution, clamps candidates to the task limit, and converts any
failure into a :class:`WorkerOutcome` so a failing worker never terminates the
query. This function is deterministic given a fixed clock.
"""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from contracts.security_context import SecurityContext
from domain.execution.errors import WorkerError
from domain.execution.models import RetrievalTask, WorkerOutcome, WorkerState
from domain.execution.worker import RetrievalWorker

_READY_TRANSITIONS = (
    WorkerState.CREATED,
    WorkerState.INITIALIZED,
    WorkerState.READY,
    WorkerState.EXECUTING,
)


def run_worker(
    worker: RetrievalWorker,
    task: RetrievalTask,
    *,
    security_context: SecurityContext | None,
    attempts: int = 1,
    clock: Callable[[], float] = perf_counter,
) -> WorkerOutcome:
    """Execute ``task`` on ``worker`` through the standard lifecycle."""
    descriptor = worker.descriptor
    transitions = list(_READY_TRANSITIONS)
    start = clock()
    try:
        candidates = tuple(worker.retrieve(task, security_context=security_context))
        clamped = candidates[: task.candidate_limit]
        transitions.append(WorkerState.COMPLETED)
        return WorkerOutcome(
            task_id=task.task_id,
            worker_id=descriptor.worker_id,
            engine=task.engine,
            state=WorkerState.COMPLETED,
            candidates=clamped,
            duration_ms=(clock() - start) * 1000.0,
            attempts=attempts,
            transitions=tuple(transitions),
        )
    except WorkerError as exc:
        transitions.append(WorkerState.FAILED)
        return _failure(
            task,
            descriptor.worker_id,
            exc.error_type,
            exc.message,
            start,
            clock,
            attempts,
            transitions,
        )
    except Exception as exc:  # noqa: BLE001 - isolate any worker failure
        transitions.append(WorkerState.FAILED)
        return _failure(
            task,
            descriptor.worker_id,
            type(exc).__name__,
            str(exc),
            start,
            clock,
            attempts,
            transitions,
        )


def _failure(
    task: RetrievalTask,
    worker_id: str,
    error_type: str,
    message: str,
    start: float,
    clock: Callable[[], float],
    attempts: int,
    transitions: list[WorkerState],
) -> WorkerOutcome:
    return WorkerOutcome(
        task_id=task.task_id,
        worker_id=worker_id,
        engine=task.engine,
        state=WorkerState.FAILED,
        error_type=error_type,
        message=message,
        duration_ms=(clock() - start) * 1000.0,
        attempts=attempts,
        transitions=tuple(transitions),
    )


def missing_worker_outcome(task: RetrievalTask) -> WorkerOutcome:
    """Return a FAILED outcome for a task that has no registered worker."""
    return WorkerOutcome(
        task_id=task.task_id,
        worker_id="",
        engine=task.engine,
        state=WorkerState.FAILED,
        error_type="unknown_worker",
        message=f"no worker registered for engine {task.engine.value!r}",
        transitions=(WorkerState.CREATED, WorkerState.FAILED),
    )


def timeout_outcome(task: RetrievalTask, worker_id: str, duration_ms: float) -> WorkerOutcome:
    """Return a TIMED_OUT outcome for a task that exceeded its budget."""
    return WorkerOutcome(
        task_id=task.task_id,
        worker_id=worker_id,
        engine=task.engine,
        state=WorkerState.TIMED_OUT,
        error_type="timeout",
        message=f"task exceeded {task.timeout_ms} ms budget",
        duration_ms=duration_ms,
        transitions=(*_READY_TRANSITIONS, WorkerState.TIMED_OUT),
    )

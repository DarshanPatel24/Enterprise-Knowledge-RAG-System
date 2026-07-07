"""Execution runtime runners (handbook Chapter 16).

Runs admitted tasks against registered workers, in parallel where possible, with
per-task timeout and bounded retry. Failures are isolated into worker outcomes
so partial failure never aborts the query. Results are returned in a
deterministic order (input task order), independent of completion order, so the
same knowledge state yields identical results.

The default :class:`ConcurrentExecutionRunner` is deterministic and offline. The
optional :class:`LangGraphExecutionRunner` runs the same tasks as a LangGraph
fan-out/fan-in graph and is selected by configuration.
"""

from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import TYPE_CHECKING, Annotated, Any, TypedDict

from contracts.security_context import SecurityContext
from domain.execution.errors import ExecutionError, ExecutionErrorType
from domain.execution.lifecycle import (
    missing_worker_outcome,
    run_worker,
    timeout_outcome,
)
from domain.execution.models import RetrievalTask, WorkerOutcome
from domain.execution.registry import WorkerRegistry

if TYPE_CHECKING:
    from collections.abc import Sequence


def _execute_with_retry(
    registry: WorkerRegistry,
    task: RetrievalTask,
    *,
    security_context: SecurityContext | None,
    max_attempts: int,
) -> WorkerOutcome:
    """Run one task with bounded retry; isolate every failure into an outcome."""
    worker = registry.get(task.engine)
    if worker is None:
        return missing_worker_outcome(task)
    outcome = run_worker(worker, task, security_context=security_context, attempts=1)
    attempt = 1
    while not outcome.succeeded and attempt < max_attempts:
        attempt += 1
        outcome = run_worker(
            worker, task, security_context=security_context, attempts=attempt
        )
    return outcome


class RetrievalExecutionRunner(ABC):
    """Executes admitted tasks and returns their worker outcomes."""

    @abstractmethod
    def run(
        self,
        tasks: Sequence[RetrievalTask],
        registry: WorkerRegistry,
        *,
        security_context: SecurityContext | None,
        max_attempts: int,
    ) -> list[WorkerOutcome]:
        """Execute the tasks and return outcomes in input task order."""


class ConcurrentExecutionRunner(RetrievalExecutionRunner):
    """Deterministic thread-pool runner with per-task timeout (default)."""

    def __init__(self, *, max_workers: int = 4) -> None:
        self._max_workers = max_workers

    def run(
        self,
        tasks: Sequence[RetrievalTask],
        registry: WorkerRegistry,
        *,
        security_context: SecurityContext | None,
        max_attempts: int,
    ) -> list[WorkerOutcome]:
        """Execute tasks in parallel; return outcomes in input order."""
        if not tasks:
            return []
        outcomes: dict[str, WorkerOutcome] = {}
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {
                pool.submit(
                    _execute_with_retry,
                    registry,
                    task,
                    security_context=security_context,
                    max_attempts=max_attempts,
                ): task
                for task in tasks
            }
            for future, task in futures.items():
                timeout_s = task.timeout_ms / 1000.0
                start = perf_counter()
                try:
                    outcomes[task.task_id] = future.result(timeout=timeout_s)
                except TimeoutError:
                    worker = registry.get(task.engine)
                    worker_id = worker.descriptor.worker_id if worker else ""
                    outcomes[task.task_id] = timeout_outcome(
                        task, worker_id, (perf_counter() - start) * 1000.0
                    )
        # Deterministic order: follow the input task order, not completion order.
        return [outcomes[task.task_id] for task in tasks]


class _GraphState(TypedDict):
    outcomes: Annotated[list[WorkerOutcome], operator.add]


class LangGraphExecutionRunner(RetrievalExecutionRunner):
    """Optional LangGraph fan-out/fan-in runner (selected by configuration)."""

    def run(
        self,
        tasks: Sequence[RetrievalTask],
        registry: WorkerRegistry,
        *,
        security_context: SecurityContext | None,
        max_attempts: int,
    ) -> list[WorkerOutcome]:
        """Execute tasks as parallel LangGraph nodes; return outcomes in order."""
        if not tasks:
            return []
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError as exc:
            raise ExecutionError(
                ExecutionErrorType.RUNNER_UNAVAILABLE,
                "langgraph is not installed; use the 'concurrent' runner",
            ) from exc

        builder = StateGraph(_GraphState)
        for task in tasks:
            builder.add_node(
                task.task_id,
                self._make_node(registry, task, security_context, max_attempts),
            )
            builder.add_edge(START, task.task_id)
            builder.add_edge(task.task_id, END)
        graph = builder.compile()
        result = graph.invoke({"outcomes": []})

        by_id = {outcome.task_id: outcome for outcome in result["outcomes"]}
        return [by_id[task.task_id] for task in tasks]

    def _make_node(
        self,
        registry: WorkerRegistry,
        task: RetrievalTask,
        security_context: SecurityContext | None,
        max_attempts: int,
    ) -> Any:  # noqa: ANN401 - langgraph node callable is untyped
        def _node(_state: _GraphState) -> dict[str, list[WorkerOutcome]]:
            outcome = _execute_with_retry(
                registry, task, security_context=security_context, max_attempts=max_attempts
            )
            return {"outcomes": [outcome]}

        return _node


def runner_from_policy(runner: str, *, max_workers: int) -> RetrievalExecutionRunner:
    """Return the configured runner (``concurrent`` default, ``langgraph`` optional)."""
    if runner == "langgraph":
        return LangGraphExecutionRunner()
    return ConcurrentExecutionRunner(max_workers=max_workers)

"""Retrieval Orchestrator (handbook Chapter 15).

The central runtime coordinator: it consumes a :class:`RetrievalPlan`, schedules
and runs the retrieval workers, collects and deduplicates candidates
deterministically, isolates failures, and produces an :class:`ExecutionSession`.
It never understands queries, ranks candidates, or assembles context.
"""

from __future__ import annotations

import uuid
from time import perf_counter

from contracts.retrieval import RetrievalCandidate
from contracts.security_context import SecurityContext
from domain.execution.errors import ExecutionError, ExecutionErrorType
from domain.execution.models import (
    ExecutionSession,
    ExecutionStatus,
    WorkerOutcome,
)
from domain.execution.policy import ExecutionPolicy
from domain.execution.registry import WorkerRegistry
from domain.execution.runner import RetrievalExecutionRunner
from domain.execution.scheduler import ExecutionScheduler
from domain.observability import get_logger
from domain.query.models import MetadataFilter, RetrievalPlan

_logger = get_logger("ekre.execution")


class RetrievalOrchestrator:
    """Coordinates worker execution for a retrieval plan."""

    def __init__(
        self,
        registry: WorkerRegistry,
        scheduler: ExecutionScheduler,
        runner: RetrievalExecutionRunner,
        *,
        policy: ExecutionPolicy,
    ) -> None:
        self._registry = registry
        self._scheduler = scheduler
        self._runner = runner
        self._policy = policy

    def execute(
        self,
        plan: RetrievalPlan,
        *,
        tenant_id: str,
        query: str = "",
        metadata_filters: tuple[MetadataFilter, ...] = (),
        security_context: SecurityContext | None = None,
        correlation_id: str | None = None,
    ) -> ExecutionSession:
        """Execute the plan and return the collected candidate session."""
        session_id = f"exec-{uuid.uuid4().hex[:12]}"
        tasks = self._scheduler.schedule(
            plan, tenant_id=tenant_id, query=query, metadata_filters=metadata_filters
        )
        if not tasks:
            raise ExecutionError(
                ExecutionErrorType.NO_TASKS_ADMITTED,
                f"no tasks admitted for plan {plan.plan_id!r}",
            )

        start = perf_counter()
        outcomes = self._runner.run(
            tasks,
            self._registry,
            security_context=security_context,
            max_attempts=self._policy.max_attempts_per_task,
        )
        duration_ms = (perf_counter() - start) * 1000.0

        candidates = _collect_candidates(outcomes)
        succeeded = sum(1 for outcome in outcomes if outcome.succeeded)
        failed = len(outcomes) - succeeded
        status = _status(succeeded, failed)

        if status is ExecutionStatus.FAILED and not self._policy.fail_open:
            raise ExecutionError(
                ExecutionErrorType.ALL_WORKERS_FAILED,
                f"all workers failed for plan {plan.plan_id!r}",
            )

        _logger.info(
            "retrieval_execution_completed",
            extra={
                "session_id": session_id,
                "plan_id": plan.plan_id,
                "status": status.value,
                "succeeded": succeeded,
                "failed": failed,
                "candidate_count": len(candidates),
            },
        )

        return ExecutionSession(
            session_id=session_id,
            plan_id=plan.plan_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            status=status,
            degraded=failed > 0,
            outcomes=tuple(outcomes),
            candidates=candidates,
            worker_count=len(outcomes),
            succeeded_count=succeeded,
            failed_count=failed,
            candidate_count=len(candidates),
            duration_ms=duration_ms,
        )


def _collect_candidates(
    outcomes: list[WorkerOutcome],
) -> tuple[RetrievalCandidate, ...]:
    """Deduplicate candidates across workers deterministically.

    Candidates are keyed by (document_id, chunk_id); the highest relevance score
    wins. The result is sorted by score (descending) then citation so ordering is
    identical regardless of worker completion order. Fusion/ranking is S4.
    """
    best: dict[tuple[str, str], RetrievalCandidate] = {}
    for outcome in outcomes:
        for candidate in outcome.candidates:
            key = (candidate.citation.document_id, candidate.citation.chunk_id)
            existing = best.get(key)
            if existing is None or candidate.relevance_score > existing.relevance_score:
                best[key] = candidate
    ordered = sorted(
        best.values(),
        key=lambda c: (
            -c.relevance_score,
            c.citation.document_id,
            c.citation.chunk_id,
        ),
    )
    return tuple(ordered)


def _status(succeeded: int, failed: int) -> ExecutionStatus:
    if failed == 0:
        return ExecutionStatus.COMPLETED
    if succeeded == 0:
        return ExecutionStatus.FAILED
    return ExecutionStatus.PARTIAL

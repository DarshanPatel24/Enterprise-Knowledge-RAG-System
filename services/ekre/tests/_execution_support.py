"""Shared builders for the retrieval execution test suite (not collected)."""

from __future__ import annotations

import time
from collections.abc import Sequence

from contracts.retrieval import Citation, RetrievalCandidate
from contracts.security_context import SecurityContext
from domain.execution import (
    RetrievalTask,
    StaticRetrievalWorker,
    WorkerDescriptor,
    WorkerError,
)
from domain.execution.worker import RetrievalWorker
from domain.query.models import (
    RankingStrategy,
    RetrievalEngineType,
    RetrievalPlan,
    RetrievalProfile,
    RetrievalStep,
)


def candidate(
    document_id: str, chunk_id: str, score: float, content: str = "text"
) -> RetrievalCandidate:
    """Build a retrieval candidate for tests."""
    return RetrievalCandidate(
        citation=Citation(
            document_id=document_id,
            chunk_id=chunk_id,
            source_path=f"/docs/{document_id}.md",
        ),
        content=content,
        relevance_score=score,
        explanation=None,
    )


def plan(
    *engines: RetrievalEngineType,
    candidate_limit: int = 5,
    timeout_ms: float = 150.0,
) -> RetrievalPlan:
    """Build a retrieval plan whose steps target ``engines``."""
    steps = tuple(
        RetrievalStep(
            engine=engine,
            candidate_limit=candidate_limit,
            timeout_ms=timeout_ms,
            parallel_group=0,
        )
        for engine in engines
    )
    return RetrievalPlan(
        plan_id="plan-test",
        profile=RetrievalProfile.BALANCED,
        steps=steps,
        ranking_strategy=RankingStrategy.HYBRID,
        total_candidate_limit=candidate_limit * len(steps),
        total_timeout_ms=500.0,
    )


def static_worker(
    engine: RetrievalEngineType, candidates: Sequence[RetrievalCandidate]
) -> StaticRetrievalWorker:
    """Build a deterministic worker returning fixed candidates."""
    return StaticRetrievalWorker(engine, candidates)


class FailingWorker(RetrievalWorker):
    """A worker that always raises a controlled WorkerError."""

    def __init__(self, engine: RetrievalEngineType) -> None:
        self._descriptor = WorkerDescriptor(
            worker_id=f"failing-{engine.value}", engine=engine
        )

    @property
    def descriptor(self) -> WorkerDescriptor:
        return self._descriptor

    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        raise WorkerError("worker_failure", "simulated worker failure")


class SlowWorker(RetrievalWorker):
    """A worker that sleeps to trigger the per-task timeout path."""

    def __init__(self, engine: RetrievalEngineType, *, delay_seconds: float) -> None:
        self._descriptor = WorkerDescriptor(
            worker_id=f"slow-{engine.value}", engine=engine
        )
        self._delay = delay_seconds

    @property
    def descriptor(self) -> WorkerDescriptor:
        return self._descriptor

    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        time.sleep(self._delay)
        return ()

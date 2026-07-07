"""Shared builders for the fusion test suite (not collected)."""

from __future__ import annotations

from collections.abc import Sequence

from contracts.retrieval import Citation, RetrievalCandidate
from domain.execution import WorkerOutcome, WorkerState
from domain.query.models import RetrievalEngineType


def candidate(
    document_id: str, chunk_id: str, score: float, *, content: str = "content"
) -> RetrievalCandidate:
    """Build a retrieval candidate."""
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


def outcome(
    engine: RetrievalEngineType,
    candidates: Sequence[RetrievalCandidate],
    *,
    worker_id: str | None = None,
    state: WorkerState = WorkerState.COMPLETED,
) -> WorkerOutcome:
    """Build a worker outcome carrying candidates."""
    return WorkerOutcome(
        task_id=f"task-{engine.value}",
        worker_id=worker_id or f"{engine.value}-worker",
        engine=engine,
        state=state,
        candidates=tuple(candidates),
    )

"""Offline demonstration of the EKRE-S2 retrieval execution core.

Runs fully offline (no Qdrant, no models): builds a query plan (S1), registers
deterministic static workers, and executes the plan through the orchestrator to
show parallel collection, deduplication, and graceful partial-failure handling.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

# Bootstrap sys.path so `src/` and the contracts package import when run directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from composition import build_query_intelligence_engine, build_retrieval_orchestrator  # noqa: E402
from config.settings import EkreSettings  # noqa: E402
from contracts.retrieval import Citation, RetrievalCandidate  # noqa: E402
from contracts.security_context import SecurityContext  # noqa: E402
from domain.execution import (  # noqa: E402
    RetrievalTask,
    StaticRetrievalWorker,
    WorkerDescriptor,
    WorkerError,
    WorkerRegistry,
)
from domain.execution.worker import RetrievalWorker  # noqa: E402
from domain.query.models import RetrievalEngineType  # noqa: E402


def _candidate(doc: str, chunk: str, score: float) -> RetrievalCandidate:
    return RetrievalCandidate(
        citation=Citation(document_id=doc, chunk_id=chunk, source_path=f"/docs/{doc}.md"),
        content=f"content of {doc}/{chunk}",
        relevance_score=score,
        explanation=None,
    )


class _FailingWorker(RetrievalWorker):
    def __init__(self, engine: RetrievalEngineType) -> None:
        self._descriptor = WorkerDescriptor(worker_id=f"failing-{engine.value}", engine=engine)

    @property
    def descriptor(self) -> WorkerDescriptor:
        return self._descriptor

    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        raise WorkerError("worker_failure", "simulated failure")


def main() -> None:
    """Run the offline EKRE-S2 execution demo."""
    settings = EkreSettings(_env_file=None)
    plan = build_query_intelligence_engine(settings).analyze(
        "compare EKIE and EKRE architecture", tenant_id="tenant-a"
    ).plan

    registry = WorkerRegistry()
    registry.register(
        StaticRetrievalWorker(
            RetrievalEngineType.VECTOR,
            [_candidate("d1", "c1", 0.92), _candidate("d2", "c2", 0.80)],
        )
    )
    registry.register(_FailingWorker(RetrievalEngineType.KEYWORD))

    orchestrator = build_retrieval_orchestrator(settings, registry=registry)
    session = orchestrator.execute(plan, tenant_id="tenant-a", query="compare EKIE and EKRE")

    print("plan:", plan.plan_id, "engines:", [s.engine.value for s in plan.steps])
    print("status:", session.status.value, "degraded:", session.degraded)
    print(
        "workers:",
        session.worker_count,
        "succeeded:",
        session.succeeded_count,
        "failed:",
        session.failed_count,
    )
    print("candidates:")
    for cand in session.candidates:
        cite = cand.citation
        print(f"  - {cite.document_id}/{cite.chunk_id} score={cand.relevance_score}")
    print("worker outcomes:")
    for outcome in session.outcomes:
        print(f"  - {outcome.engine.value}: {outcome.state.value} ({outcome.error_type or 'ok'})")


if __name__ == "__main__":
    main()

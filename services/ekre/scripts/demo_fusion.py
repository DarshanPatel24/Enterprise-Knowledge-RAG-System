"""Offline demonstration of the EKRE-S4 candidate collection and fusion.

Runs fully offline: simulates worker outcomes where the same document is found by
multiple engines, then collects them into a Unified Candidate Set and fuses them
into Knowledge Objects, showing RRF scoring and preserved evidence provenance.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path so `src/` and the contracts package import when run directly.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from composition import build_candidate_collector, build_candidate_fusion  # noqa: E402
from config.settings import EkreSettings  # noqa: E402
from contracts.retrieval import Citation, RetrievalCandidate  # noqa: E402
from domain.execution import WorkerOutcome, WorkerState  # noqa: E402
from domain.query.models import RetrievalEngineType  # noqa: E402


def _candidate(doc: str, chunk: str, score: float) -> RetrievalCandidate:
    return RetrievalCandidate(
        citation=Citation(document_id=doc, chunk_id=chunk, source_path=f"/docs/{doc}.md"),
        content=f"content of {doc}/{chunk}",
        relevance_score=score,
        explanation=None,
    )


def _outcome(engine: RetrievalEngineType, candidates: list) -> WorkerOutcome:
    return WorkerOutcome(
        task_id=f"task-{engine.value}",
        worker_id=f"{engine.value}-worker",
        engine=engine,
        state=WorkerState.COMPLETED,
        candidates=tuple(candidates),
    )


def main() -> None:
    """Run the offline EKRE-S4 fusion demo."""
    settings = EkreSettings(_env_file=None)
    outcomes = [
        _outcome(
            RetrievalEngineType.VECTOR,
            [_candidate("sop", "c1", 0.92), _candidate("guide", "c1", 0.70)],
        ),
        _outcome(RetrievalEngineType.KEYWORD, [_candidate("sop", "c1", 0.80)]),
        _outcome(RetrievalEngineType.METADATA, [_candidate("sop", "c1", 0.60)]),
    ]

    unified = build_candidate_collector().collect(outcomes)
    fused = build_candidate_fusion(settings).fuse(unified)

    print("Unified Candidate Set:")
    print("  total:", unified.total, "sources:", unified.source_counts)
    print("Fused Knowledge Set (policy:", fused.policy.value, "):")
    for obj in fused.objects:
        engines = [e.value for e in obj.source_engines]
        print(
            f"  - {obj.knowledge_id} fusion={obj.fusion_score:.5f} "
            f"best={obj.best_score:.2f} engines={engines}"
        )


if __name__ == "__main__":
    main()

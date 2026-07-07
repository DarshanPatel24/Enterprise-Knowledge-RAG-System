"""Offline demonstration of the EKRE-S8 readiness and NFR validation.

Runs fully offline: assesses deployment readiness, evaluates retrieval accuracy
(Precision@k / Recall@k / MRR / NDCG) against a small labeled set, and produces
the EKCP handoff readiness report over a citation-preserving package.
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

from composition import build_deployment_readiness  # noqa: E402
from config.settings import EkreSettings  # noqa: E402
from contracts.retrieval import Citation, RetrievalCandidate, RetrievalContextPackage  # noqa: E402
from domain.evaluation import QueryJudgment, evaluate  # noqa: E402
from domain.governance import build_retrieval_trace  # noqa: E402
from domain.observability import LatencyBreakdown  # noqa: E402
from domain.readiness import assess_handoff_readiness  # noqa: E402


def main() -> None:
    """Run the offline EKRE-S8 readiness demo."""
    settings = EkreSettings(_env_file=None)

    print("Deployment readiness:")
    deployment = build_deployment_readiness(settings)
    for finding in deployment.findings:
        print(f"  [{finding.severity.value:7s}] {finding.check}: {finding.message}")
    print("  ready:", deployment.ready)

    print("\nAccuracy validation (k=10):")
    judgments = [
        QueryJudgment(query_id="q1", relevant_ids=frozenset({"sop:c1"})),
        QueryJudgment(query_id="q2", relevant_ids=frozenset({"guide:c1", "policy:c1"})),
    ]
    results = {"q1": ["sop:c1", "guide:c1"], "q2": ["guide:c1", "x:c1", "policy:c1"]}
    report = evaluate(
        judgments,
        results,
        k=settings.deployment.eval_k,
        thresholds={
            "precision": settings.deployment.min_precision_at_k,
            "recall": settings.deployment.min_recall_at_k,
            "mrr": settings.deployment.min_mrr,
            "ndcg": settings.deployment.min_ndcg,
        },
    )
    print(
        f"  P@{report.k}={report.mean_precision_at_k:.3f} "
        f"R@{report.k}={report.mean_recall_at_k:.3f}"
    )
    print(f"  MRR={report.mean_reciprocal_rank:.3f} NDCG={report.mean_ndcg_at_k:.3f}")
    print("  meets thresholds:", report.meets_thresholds)

    print("\nEKCP handoff readiness:")
    package = RetrievalContextPackage(
        query="compare EKIE and EKRE",
        tenant_id="tenant-a",
        candidates=[
            RetrievalCandidate(
                citation=Citation(document_id="sop", chunk_id="c1", source_path="/docs/sop.md"),
                content="content",
                relevance_score=0.83,
                explanation="composite=0.83",
            )
        ],
        security_filtered=True,
    )
    trace = build_retrieval_trace(
        LatencyBreakdown(stages={"execution": 42.0}, total_ms=42.0),
        execution_id="exec-demo",
        trace_id="trace-demo",
        tenant_id="tenant-a",
        budget_ms=settings.deployment.max_latency_ms,
    )
    handoff = assess_handoff_readiness(
        package,
        trace=trace,
        evaluation=report,
        max_latency_ms=settings.deployment.max_latency_ms,
    )
    for finding in handoff.findings:
        print(f"  [{finding.severity.value:7s}] {finding.check}: {finding.message}")
    print("  ready for EKCP handoff:", handoff.ready)


if __name__ == "__main__":
    main()

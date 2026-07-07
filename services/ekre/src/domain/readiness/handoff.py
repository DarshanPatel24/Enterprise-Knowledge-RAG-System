"""EKCP handoff readiness assessment (handbook Chapter 27, Chapter 5).

Proves that the Retrieval Context Package is ready to hand to EKCP: citation
lineage is complete, the result is security-filtered, latency is within the NFR
budget, and accuracy meets the configured thresholds. Advisory report; it never
changes the package.
"""

from __future__ import annotations

from contracts.retrieval import RetrievalContextPackage
from domain.evaluation import EvaluationReport
from domain.governance import RetrievalTrace
from domain.readiness.models import ReadinessReport, error, info, warning


def assess_handoff_readiness(
    package: RetrievalContextPackage,
    *,
    trace: RetrievalTrace | None = None,
    evaluation: EvaluationReport | None = None,
    max_latency_ms: float = 500.0,
) -> ReadinessReport:
    """Assess whether the handoff package is ready for EKCP consumption."""
    findings = []

    missing_citations = [
        candidate
        for candidate in package.candidates
        if not (
            candidate.citation.document_id
            and candidate.citation.chunk_id
            and candidate.citation.source_path
        )
    ]
    if missing_citations:
        findings.append(
            error("citation_persistence", f"{len(missing_citations)} candidates missing citation")
        )
    else:
        findings.append(
            info("citation_persistence", f"{len(package.candidates)} candidates fully cited")
        )

    if package.security_filtered:
        findings.append(info("security", "result is security-filtered"))
    else:
        findings.append(error("security", "result is not security-filtered"))

    if trace is not None:
        if trace.total_ms > max_latency_ms:
            findings.append(
                warning(
                    "latency",
                    f"latency {trace.total_ms:.1f} ms exceeds {max_latency_ms} ms budget",
                )
            )
        else:
            findings.append(info("latency", f"latency {trace.total_ms:.1f} ms within budget"))

    if evaluation is not None:
        if evaluation.meets_thresholds:
            findings.append(
                info("accuracy", f"accuracy thresholds met at k={evaluation.k}")
            )
        else:
            findings.append(
                warning("accuracy", "accuracy thresholds not met for the evaluation set")
            )

    return ReadinessReport(name="ekcp_handoff", findings=tuple(findings))

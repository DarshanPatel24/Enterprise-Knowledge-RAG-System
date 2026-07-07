"""Tests for deployment and EKCP handoff readiness assessments."""

from __future__ import annotations

from config.settings import DeploymentSettings
from contracts.retrieval import Citation, RetrievalCandidate, RetrievalContextPackage
from domain.evaluation import evaluate
from domain.governance import build_retrieval_trace
from domain.observability import LatencyBreakdown
from domain.readiness import assess_deployment_readiness, assess_handoff_readiness


def test_deployment_readiness_defaults_are_ready() -> None:
    report = assess_deployment_readiness(DeploymentSettings(_env_file=None))
    assert report.name == "deployment"
    assert report.ready is True


def test_deployment_readiness_warns_on_single_replica() -> None:
    report = assess_deployment_readiness(DeploymentSettings(_env_file=None, replicas=1))
    checks = {f.check: f.severity.value for f in report.findings}
    assert checks["high_availability"] == "warning"
    assert report.ready is True  # warnings do not block


def _package(*, security_filtered: bool = True) -> RetrievalContextPackage:
    return RetrievalContextPackage(
        query="q",
        tenant_id="tenant-a",
        candidates=[
            RetrievalCandidate(
                citation=Citation(document_id="d1", chunk_id="c1", source_path="/d1.md"),
                content="text",
                relevance_score=0.9,
                explanation=None,
            )
        ],
        security_filtered=security_filtered,
    )


def test_handoff_ready_with_citations_and_security() -> None:
    trace = build_retrieval_trace(
        LatencyBreakdown(stages={"execution": 40.0}, total_ms=40.0),
        execution_id="e1",
        trace_id="t1",
        tenant_id="tenant-a",
        budget_ms=500.0,
    )
    report = assess_handoff_readiness(_package(), trace=trace, max_latency_ms=500.0)
    assert report.name == "ekcp_handoff"
    assert report.ready is True


def test_handoff_blocks_when_not_security_filtered() -> None:
    report = assess_handoff_readiness(_package(security_filtered=False))
    assert report.ready is False


def test_handoff_warns_on_latency_and_accuracy() -> None:
    trace = build_retrieval_trace(
        LatencyBreakdown(stages={"execution": 600.0}, total_ms=600.0),
        execution_id="e1",
        trace_id="t1",
        tenant_id="tenant-a",
        budget_ms=500.0,
    )
    evaluation = evaluate([], {}, k=10, thresholds={"precision": 0.5})
    report = assess_handoff_readiness(
        _package(), trace=trace, evaluation=evaluation, max_latency_ms=500.0
    )
    severities = {f.check: f.severity.value for f in report.findings}
    assert severities["latency"] == "warning"
    # Empty evaluation set meets thresholds vacuously -> accuracy info.
    assert report.ready is True

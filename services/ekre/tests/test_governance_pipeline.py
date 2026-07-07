"""End-to-end tests for the traced, audited, masked retrieval pipeline."""

from __future__ import annotations

from _retrieval_support import ADAPTER, connector, indexed, security_context

from composition import (
    build_candidate_collector,
    build_candidate_fusion,
    build_context_assembly_engine,
    build_masker,
    build_query_intelligence_engine,
    build_ranking_engine,
    build_retrieval_orchestrator,
)
from config.settings import EkreSettings
from contracts.enums import ClassificationClearance
from domain.governance import InMemoryAuditSink, RetrievalPipeline


def _pipeline(conn: object, sink: InMemoryAuditSink) -> RetrievalPipeline:
    settings = EkreSettings(_env_file=None)
    from domain.retrieval import build_worker_registry

    registry = build_worker_registry(
        conn, ADAPTER, collection="enterprise_documents", require_security_context=True
    )
    orchestrator = build_retrieval_orchestrator(settings, registry=registry)
    return RetrievalPipeline(
        build_query_intelligence_engine(settings),
        orchestrator,
        build_candidate_collector(),
        build_candidate_fusion(settings),
        build_ranking_engine(settings),
        build_context_assembly_engine(settings),
        build_masker(settings),
        sink,
        budget_ms=500.0,
        enable_audit=True,
        policy_version="v1",
    )


def test_pipeline_records_timeline_and_audit() -> None:
    sink = InMemoryAuditSink()
    conn = connector(indexed("d1", "c1", "compare EKIE and EKRE architecture"))
    result = _pipeline(conn, sink).retrieve(
        "compare EKIE and EKRE architecture",
        tenant_id="tenant-a",
        security_context=security_context(ClassificationClearance.INTERNAL),
    )
    stages = {s.stage for s in result.trace.stages}
    assert {
        "query_understanding",
        "execution",
        "fusion",
        "ranking",
        "assembly",
        "masking",
    } <= stages
    assert result.trace.execution_id.startswith("exec-")
    assert len(sink.history()) == 1
    assert sink.history()[0].actor == "analyst-1"
    assert result.package.candidates


def test_pipeline_masks_pii_before_handoff() -> None:
    sink = InMemoryAuditSink()
    conn = connector(indexed("d1", "c1", "contact john@acme.com about EKRE"))
    result = _pipeline(conn, sink).retrieve(
        "EKRE",
        tenant_id="tenant-a",
        security_context=security_context(ClassificationClearance.INTERNAL),
    )
    assert result.package.candidates
    contents = " ".join(c.content for c in result.package.candidates)
    assert "john@acme.com" not in contents
    assert result.trace.redactions >= 1

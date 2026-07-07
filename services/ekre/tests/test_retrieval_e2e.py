"""End-to-end retrieval: plan (S1) -> execute (S2) -> workers (S3)."""

from __future__ import annotations

from _retrieval_support import ADAPTER, connector, indexed, security_context

from composition import build_query_intelligence_engine, build_retrieval_orchestrator
from config.settings import EkreSettings
from contracts.enums import ClassificationClearance
from domain.execution import ExecutionStatus
from domain.retrieval import build_worker_registry


def _settings() -> EkreSettings:
    return EkreSettings(_env_file=None)


def test_end_to_end_retrieval_collects_candidates() -> None:
    settings = _settings()
    conn = connector(
        indexed("d1", "c1", "compare EKIE and EKRE architecture"),
        indexed("d2", "c2", "unrelated topic"),
    )
    registry = build_worker_registry(
        conn, ADAPTER, collection="enterprise_documents", require_security_context=True
    )
    orchestrator = build_retrieval_orchestrator(settings, registry=registry)

    structured = build_query_intelligence_engine(settings).analyze(
        "compare EKIE and EKRE architecture", tenant_id="tenant-a"
    )
    session = orchestrator.execute(
        structured.plan,
        tenant_id="tenant-a",
        query=structured.understanding.normalized_query,
        metadata_filters=structured.understanding.metadata_filters,
        security_context=security_context(ClassificationClearance.INTERNAL),
    )
    assert session.status is ExecutionStatus.COMPLETED
    assert session.candidate_count >= 1
    assert any(c.citation.document_id == "d1" for c in session.candidates)


def test_end_to_end_clearance_isolation() -> None:
    settings = _settings()
    conn = connector(
        indexed("d1", "c1", "compare EKIE and EKRE", clearance="restricted"),
    )
    registry = build_worker_registry(
        conn, ADAPTER, collection="enterprise_documents", require_security_context=True
    )
    orchestrator = build_retrieval_orchestrator(settings, registry=registry)

    structured = build_query_intelligence_engine(settings).analyze(
        "compare EKIE and EKRE", tenant_id="tenant-a"
    )
    session = orchestrator.execute(
        structured.plan,
        tenant_id="tenant-a",
        query=structured.understanding.normalized_query,
        security_context=security_context(ClassificationClearance.PUBLIC),
    )
    # A public user must never see the restricted document.
    assert all(c.citation.document_id != "d1" for c in session.candidates)

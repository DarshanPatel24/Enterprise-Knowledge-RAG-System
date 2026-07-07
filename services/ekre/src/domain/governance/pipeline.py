"""Traced, audited, masked retrieval pipeline (handbook Chapters 28-29).

The single production entry point that runs the full EKRE pipeline --- query
intelligence, execution, fusion, ranking, assembly --- while recording an
end-to-end execution trace, auditing the authorization decision, and masking
sensitive content before the EKCP handoff. It composes existing engines and adds
cross-cutting observability and governance; it changes no retrieval logic.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from contracts.retrieval import RetrievalContextPackage
from contracts.security_context import SecurityContext
from domain.assembly import ContextAssemblyEngine, ContextMetrics
from domain.execution import RetrievalOrchestrator
from domain.fusion import CandidateCollector, CandidateFusion
from domain.governance.audit import (
    AuditAction,
    AuditResult,
    AuditSink,
    build_audit_record,
)
from domain.governance.masking import Masker
from domain.governance.trace import RetrievalTrace, build_retrieval_trace
from domain.observability import LatencyRecorder, get_correlation_id, get_logger
from domain.query import QueryIntelligenceEngine
from domain.ranking import RankingEngine

_logger = get_logger("ekre.pipeline")


class TracedRetrieval(BaseModel):
    """The full retrieval result: handoff package, metrics, and execution trace."""

    model_config = ConfigDict(frozen=True)

    package: RetrievalContextPackage
    metrics: ContextMetrics
    trace: RetrievalTrace


class RetrievalPipeline:
    """Runs the full pipeline with tracing, audit, and masking."""

    def __init__(
        self,
        query_engine: QueryIntelligenceEngine,
        orchestrator: RetrievalOrchestrator,
        collector: CandidateCollector,
        fusion: CandidateFusion,
        ranking: RankingEngine,
        assembly: ContextAssemblyEngine,
        masker: Masker,
        audit_sink: AuditSink,
        *,
        budget_ms: float,
        enable_audit: bool,
        policy_version: str,
    ) -> None:
        self._query_engine = query_engine
        self._orchestrator = orchestrator
        self._collector = collector
        self._fusion = fusion
        self._ranking = ranking
        self._assembly = assembly
        self._masker = masker
        self._audit_sink = audit_sink
        self._budget_ms = budget_ms
        self._enable_audit = enable_audit
        self._policy_version = policy_version

    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str,
        security_context: SecurityContext,
        language: str | None = None,
    ) -> TracedRetrieval:
        """Execute the full traced, audited, masked retrieval pipeline."""
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"
        correlation_id = get_correlation_id()
        recorder = LatencyRecorder()

        with recorder.stage("query_understanding"):
            structured = self._query_engine.analyze(
                query, tenant_id=tenant_id, language=language
            )
        with recorder.stage("execution"):
            session = self._orchestrator.execute(
                structured.plan,
                tenant_id=tenant_id,
                query=structured.understanding.normalized_query,
                metadata_filters=structured.understanding.metadata_filters,
                security_context=security_context,
            )
        with recorder.stage("fusion"):
            fused = self._fusion.fuse(self._collector.collect(session.outcomes))
        with recorder.stage("ranking"):
            ranked = self._ranking.rank(
                fused, query=structured.understanding.normalized_query
            )
        with recorder.stage("assembly"):
            assembled = self._assembly.assemble(
                ranked,
                query=structured.understanding.normalized_query,
                tenant_id=tenant_id,
                security_filtered=True,
            )
        with recorder.stage("masking"):
            package, redactions = self._masker.mask_package(assembled.package)

        self._audit(
            security_context, tenant_id, execution_id, correlation_id, package, redactions
        )
        trace = build_retrieval_trace(
            recorder.breakdown(),
            execution_id=execution_id,
            trace_id=correlation_id or execution_id,
            tenant_id=tenant_id,
            budget_ms=self._budget_ms,
            correlation_id=correlation_id,
            redactions=redactions,
            policy_version=self._policy_version,
        )
        return TracedRetrieval(package=package, metrics=assembled.metrics, trace=trace)

    def _audit(
        self,
        security_context: SecurityContext,
        tenant_id: str,
        execution_id: str,
        correlation_id: str | None,
        package: RetrievalContextPackage,
        redactions: int,
    ) -> None:
        if not self._enable_audit:
            return
        self._audit_sink.record(
            build_audit_record(
                action=AuditAction.RETRIEVE,
                result=AuditResult.ALLOWED,
                actor=security_context.user_id,
                tenant_id=tenant_id,
                execution_id=execution_id,
                correlation_id=correlation_id,
                policy_version=self._policy_version,
                detail={
                    "clearance": security_context.classification_clearance.value,
                    "candidates": str(len(package.candidates)),
                    "redactions": str(redactions),
                },
            )
        )

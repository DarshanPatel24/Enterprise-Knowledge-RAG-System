"""Offline demonstration of the EKRE-S7 observability + governance pipeline.

Runs the full pipeline offline with an in-memory connector: shows the end-to-end
execution trace (per-stage timeline), the security audit trail, and PII masking
applied to the handoff package before it would be handed to EKCP.
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

from composition import (  # noqa: E402
    build_candidate_collector,
    build_candidate_fusion,
    build_context_assembly_engine,
    build_masker,
    build_query_intelligence_engine,
    build_ranking_engine,
    build_retrieval_orchestrator,
)
from config.settings import EkreSettings  # noqa: E402
from contracts.enums import ClassificationClearance  # noqa: E402
from contracts.security_context import SecurityContext  # noqa: E402
from domain.connectors import IndexedDocument, InMemoryRepositoryConnector  # noqa: E402
from domain.governance import InMemoryAuditSink, RetrievalPipeline  # noqa: E402
from domain.retrieval import LocalHashEmbeddingAdapter, build_worker_registry  # noqa: E402


def main() -> None:
    """Run the offline EKRE-S7 observability + governance demo."""
    settings = EkreSettings(_env_file=None)
    adapter = LocalHashEmbeddingAdapter(settings.workers.local_embedding_dimension)
    text = "Compare EKIE and EKRE. Contact john@acme.com or SSN 123-45-6789."
    connector = InMemoryRepositoryConnector(
        [
            IndexedDocument(
                document_id="sop",
                chunk_id="c1",
                content=text,
                source_path="/docs/sop.md",
                vector=adapter.embed(text),
                classification_clearance="internal",
            )
        ]
    )
    registry = build_worker_registry(
        connector, adapter, collection="enterprise_documents", require_security_context=True
    )
    sink = InMemoryAuditSink()
    pipeline = RetrievalPipeline(
        build_query_intelligence_engine(settings),
        build_retrieval_orchestrator(settings, registry=registry),
        build_candidate_collector(),
        build_candidate_fusion(settings),
        build_ranking_engine(settings),
        build_context_assembly_engine(settings),
        build_masker(settings),
        sink,
        budget_ms=settings.governance.total_latency_budget_ms,
        enable_audit=True,
        policy_version=settings.governance.policy_version,
    )

    context = SecurityContext(
        user_id="analyst-1",
        tenant_id="tenant-a",
        classification_clearance=ClassificationClearance.INTERNAL,
    )
    result = pipeline.retrieve(
        "compare EKIE and EKRE architecture", tenant_id="tenant-a", security_context=context
    )

    print("Execution trace:", result.trace.execution_id)
    for stage in result.trace.stages:
        print(f"  {stage.stage:20s} {stage.duration_ms:8.3f} ms")
    print(f"  {'total':20s} {result.trace.total_ms:8.3f} ms (budget {result.trace.budget_ms})")
    print("  redactions:", result.trace.redactions, "over_budget:", result.trace.over_budget)
    print("Masked handoff candidates:")
    for candidate in result.package.candidates:
        print(f"  - {candidate.citation.document_id}: {candidate.content}")
    print("Audit trail:")
    for record in sink.history():
        print(
            f"  - {record.action.value} {record.result.value} "
            f"actor={record.actor} {record.detail}"
        )


if __name__ == "__main__":
    main()

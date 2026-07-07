"""Offline demonstration of the EKRE-S3 retrieval workers.

Runs fully offline (in-memory connector + deterministic hash embedder): indexes
a few documents at different clearances, then plans (S1) and executes (S2) a
query through the real vector/keyword/metadata workers, showing candidate
collection and pre-pool security filtering.
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
    build_query_intelligence_engine,
    build_retrieval_orchestrator,
)
from config.settings import EkreSettings  # noqa: E402
from contracts.enums import ClassificationClearance  # noqa: E402
from contracts.security_context import SecurityContext  # noqa: E402
from domain.connectors import IndexedDocument, InMemoryRepositoryConnector  # noqa: E402
from domain.retrieval import LocalHashEmbeddingAdapter, build_worker_registry  # noqa: E402


def main() -> None:
    """Run the offline EKRE-S3 retrieval demo."""
    settings = EkreSettings(_env_file=None)
    adapter = LocalHashEmbeddingAdapter(settings.workers.local_embedding_dimension)

    texts = {
        "d1": ("compare EKIE and EKRE architecture", "public"),
        "d2": ("internal deployment runbook", "internal"),
        "d3": ("restricted incident report", "restricted"),
    }
    connector = InMemoryRepositoryConnector(
        [
            IndexedDocument(
                document_id=doc_id,
                chunk_id="c1",
                content=text,
                source_path=f"/docs/{doc_id}.md",
                vector=adapter.embed(text),
                classification_clearance=clearance,
            )
            for doc_id, (text, clearance) in texts.items()
        ]
    )
    registry = build_worker_registry(
        connector, adapter, collection="enterprise_documents", require_security_context=True
    )
    orchestrator = build_retrieval_orchestrator(settings, registry=registry)

    structured = build_query_intelligence_engine(settings).analyze(
        "compare EKIE and EKRE architecture", tenant_id="tenant-a"
    )

    for clearance in (ClassificationClearance.PUBLIC, ClassificationClearance.RESTRICTED):
        context = SecurityContext(
            user_id="analyst-1", tenant_id="tenant-a", classification_clearance=clearance
        )
        session = orchestrator.execute(
            structured.plan,
            tenant_id="tenant-a",
            query=structured.understanding.normalized_query,
            security_context=context,
        )
        print("=" * 60)
        print("clearance:", clearance.value, "status:", session.status.value)
        print("candidates:")
        for cand in session.candidates:
            print(f"  - {cand.citation.document_id} score={cand.relevance_score:.3f}")


if __name__ == "__main__":
    main()

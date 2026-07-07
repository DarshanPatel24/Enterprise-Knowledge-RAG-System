"""Offline demonstration of the EKRE-S6 context assembly + packaging.

Runs fully offline: builds a ranked knowledge set, assembles it into the
citation-preserving Retrieval Context Package handed to EKCP, and prints the
package candidates (with citations) and the assembly metrics.
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

from composition import build_context_assembly_engine  # noqa: E402
from config.settings import EkreSettings  # noqa: E402
from contracts.retrieval import Citation  # noqa: E402
from domain.fusion import EvidenceSource, KnowledgeObject  # noqa: E402
from domain.query.models import RetrievalEngineType  # noqa: E402
from domain.ranking.models import RankedKnowledgeObject, RankedKnowledgeSet  # noqa: E402


def _ranked(doc: str, content: str, composite: float, rank: int) -> RankedKnowledgeObject:
    ko = KnowledgeObject(
        knowledge_id=f"ko-{doc}",
        citation=Citation(document_id=doc, chunk_id="c1", source_path=f"/docs/{doc}.md"),
        content=content,
        evidence=(
            EvidenceSource(
                engine=RetrievalEngineType.VECTOR, worker_id="vector-w", score=composite, rank=0
            ),
        ),
        source_engines=(RetrievalEngineType.VECTOR,),
        fusion_score=composite,
        best_score=composite,
    )
    return RankedKnowledgeObject(
        knowledge_object=ko,
        rank=rank,
        composite_score=composite,
        factor_scores={"semantic": composite},
        factor_weights={"semantic": 1.0},
        explanation=f"composite={composite:.4f}",
    )


def main() -> None:
    """Run the offline EKRE-S6 assembly demo."""
    settings = EkreSettings(_env_file=None)
    rks = RankedKnowledgeSet(
        ranking_id="rks-demo",
        policy_version="v1",
        object_count=2,
        considered_count=2,
        objects=(
            _ranked("sop", "Refinery shutdown standard operating procedure.", 0.83, 1),
            _ranked("guide", "Deployment guide overview.", 0.38, 2),
        ),
    )

    result = build_context_assembly_engine(settings).assemble(
        rks, query="compare EKIE and EKRE", tenant_id="tenant-a"
    )
    print("Retrieval Context Package (EKCP handoff):")
    print("  query:", result.package.query, "security_filtered:", result.package.security_filtered)
    for candidate in result.package.candidates:
        cite = candidate.citation
        print(
            f"  - {cite.document_id}/{cite.chunk_id} [{cite.source_path}] "
            f"score={candidate.relevance_score}"
        )
    m = result.metrics
    print(
        "Metrics:",
        f"selected={m.selected_count}/{m.considered_count}",
        f"tokens={m.total_tokens}/{m.token_budget}",
        f"ordering={m.ordering}",
    )


if __name__ == "__main__":
    main()

"""Offline demonstration of the EKRE-S5 ranking engine.

Runs fully offline: builds fused knowledge objects with different evidence, then
ranks them with the deterministic evidence-weighted engine, printing the ordered
result with the full ranking audit trail (factor scores, weights, composite).
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

from composition import build_ranking_engine  # noqa: E402
from config.settings import EkreSettings  # noqa: E402
from contracts.retrieval import Citation  # noqa: E402
from domain.fusion import (  # noqa: E402
    EvidenceSource,
    FusedKnowledgeSet,
    FusionPolicy,
    KnowledgeObject,
)
from domain.query.models import RetrievalEngineType  # noqa: E402


def _obj(doc: str, evidences: list, fusion: float) -> KnowledgeObject:
    evidence = tuple(
        EvidenceSource(engine=e, worker_id=f"{e.value}-w", score=s, rank=r)
        for e, s, r in evidences
    )
    return KnowledgeObject(
        knowledge_id=f"ko-{doc}",
        citation=Citation(document_id=doc, chunk_id="c1", source_path=f"/docs/{doc}.md"),
        content=f"content of {doc}",
        evidence=evidence,
        source_engines=tuple(dict.fromkeys(e for e, _, _ in evidences)),
        fusion_score=fusion,
        best_score=max(s for _, s, _ in evidences),
    )


def main() -> None:
    """Run the offline EKRE-S5 ranking demo."""
    settings = EkreSettings(_env_file=None)
    fused = FusedKnowledgeSet(
        fusion_id="fks-demo",
        policy=FusionPolicy.CHUNK_IDENTITY,
        object_count=3,
        objects=(
            _obj(
                "sop",
                [(RetrievalEngineType.VECTOR, 0.92, 0), (RetrievalEngineType.KEYWORD, 0.8, 0)],
                0.049,
            ),
            _obj("guide", [(RetrievalEngineType.VECTOR, 0.7, 1)], 0.016),
            _obj("policy", [(RetrievalEngineType.METADATA, 0.6, 0)], 0.016),
        ),
    )

    rks = build_ranking_engine(settings).rank(fused, query="compare EKIE and EKRE")
    print("Ranked Knowledge Set (policy:", rks.policy_version, "reranked:", rks.reranked, ")")
    print("considered:", rks.considered_count, "returned:", rks.object_count)
    for obj in rks.objects:
        print(f"  #{obj.rank} {obj.knowledge_object.knowledge_id}")
        print(f"     {obj.explanation}")


if __name__ == "__main__":
    main()

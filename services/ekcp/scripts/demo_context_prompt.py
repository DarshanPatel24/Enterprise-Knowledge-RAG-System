"""Offline demo of the EKCP S2 context and prompt orchestration.

Runs fully offline (no server, no network). Demonstrates assembling a governed
Execution Context Package from conversation history and enterprise evidence, and
constructing a governed prompt with explicit named variables and preserved
citations.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path so `src/` packages import when run as a script.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from composition import (  # noqa: E402
    build_context_assembler,
    build_prompt_orchestrator,
    configure_observability,
)
from config.settings import EkcpSettings  # noqa: E402
from contracts.retrieval import (  # noqa: E402
    Citation,
    RetrievalCandidate,
    RetrievalContextPackage,
)
from domain.context import ContextItem, ContextSource  # noqa: E402


def main() -> None:
    """Exercise the S2 context and prompt orchestration, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)
    assembler = build_context_assembler(settings)
    orchestrator = build_prompt_orchestrator(settings)

    retrieval = RetrievalContextPackage(
        query="remote work policy",
        tenant_id="tenant-a",
        candidates=[
            RetrievalCandidate(
                citation=Citation(
                    document_id="d1", chunk_id="c1", source_path="/docs/hr-policy.md"
                ),
                content="Employees may work remotely up to two days per week.",
                relevance_score=0.94,
                explanation="matched remote work policy",
            ),
        ],
    )
    policy_items = (
        ContextItem(
            source=ContextSource.POLICY,
            content="Never disclose salary or personal data.",
            reason="policy constraint",
            rank_score=1.0,
        ),
    )

    ecp = assembler.assemble(
        tenant_id="tenant-a",
        conversation_id="conv-1",
        user_intent="What is our remote work policy?",
        conversation_history=("Hi", "I have an HR question"),
        retrieval=retrieval,
        policy_items=policy_items,
    )
    print("Context package:", ecp.context_id)
    print(
        "Selected:", ecp.metrics.selected_count,
        "tokens:", ecp.metrics.total_tokens,
        "sources:", ecp.metrics.source_diversity,
    )

    package = orchestrator.build(ecp)
    print("Prompt package:", package.prompt_id, "status:", package.validation_status)
    print("--- prompt text ---")
    print(package.prompt_text)


if __name__ == "__main__":
    main()

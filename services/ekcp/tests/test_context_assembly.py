"""Tests for context assembly: ranking, budgeting, citations, governance."""

from __future__ import annotations

from config.settings import ContextSettings
from contracts.retrieval import (
    Citation,
    RetrievalCandidate,
    RetrievalContextPackage,
)
from domain.context import (
    ContextAssembler,
    ContextItem,
    ContextPolicy,
    ContextSource,
    estimate_tokens,
)


def _assembler(**overrides: object) -> ContextAssembler:
    settings = ContextSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return ContextAssembler(ContextPolicy.from_settings(settings))


def _retrieval(*candidates: RetrievalCandidate) -> RetrievalContextPackage:
    return RetrievalContextPackage(
        query="q", tenant_id="tenant-a", candidates=list(candidates)
    )


def _candidate(
    content: str, score: float, *, source_path: str = "/docs/a.md"
) -> RetrievalCandidate:
    return RetrievalCandidate(
        citation=Citation(document_id="d1", chunk_id="c1", source_path=source_path),
        content=content,
        relevance_score=score,
    )


def test_estimate_tokens() -> None:
    assert estimate_tokens("", chars_per_token=4) == 0
    assert estimate_tokens("12345678", chars_per_token=4) == 2


def test_assemble_ranks_and_preserves_citations() -> None:
    package = _assembler().assemble(
        tenant_id="tenant-a",
        conversation_id="conv-1",
        user_intent="remote work policy",
        conversation_history=("hello", "what is the policy"),
        retrieval=_retrieval(_candidate("Remote work is allowed twice a week", 0.9)),
    )
    assert package.metrics.selected_count == 3
    enterprise = [i for i in package.items if i.source is ContextSource.ENTERPRISE]
    assert enterprise and enterprise[0].citation is not None
    assert package.metrics.source_diversity == 2


def test_citation_unready_candidate_is_dropped() -> None:
    # An empty content candidate is not citation-ready and must be stripped.
    package = _assembler().assemble(
        tenant_id="tenant-a",
        conversation_id="conv-1",
        user_intent="policy",
        retrieval=_retrieval(
            _candidate("valid evidence", 0.8),
            RetrievalCandidate(
                citation=Citation(document_id="d2", chunk_id="c2", source_path="/x.md"),
                content="   ",
                relevance_score=0.7,
            ),
        ),
    )
    assert package.metrics.dropped_citation_unready == 1
    assert any("unready citations" in w for w in package.warnings)


def test_min_relevance_filter() -> None:
    package = _assembler(min_relevance=0.5).assemble(
        tenant_id="tenant-a",
        conversation_id="conv-1",
        user_intent="policy",
        retrieval=_retrieval(_candidate("low", 0.2), _candidate("high", 0.95)),
    )
    contents = [i.content for i in package.items]
    assert "high" in contents
    assert "low" not in contents
    assert package.metrics.dropped_below_relevance == 1


def test_dedupe_content() -> None:
    package = _assembler().assemble(
        tenant_id="tenant-a",
        conversation_id="conv-1",
        user_intent="policy",
        retrieval=_retrieval(_candidate("same text", 0.9), _candidate("same text", 0.8)),
    )
    assert package.metrics.dropped_duplicates == 1


def test_policy_items_always_included_and_budget_degrades() -> None:
    long_text = "word " * 500
    package = _assembler(max_context_tokens=40, reserve_ratio=0.0).assemble(
        tenant_id="tenant-a",
        conversation_id="conv-1",
        user_intent="policy",
        retrieval=_retrieval(_candidate(long_text, 0.9), _candidate(long_text + "x", 0.8)),
        policy_items=(
            ContextItem(
                source=ContextSource.POLICY,
                content="Do not share confidential data.",
                reason="policy",
                rank_score=1.0,
            ),
        ),
    )
    policy_items = [i for i in package.items if i.source is ContextSource.POLICY]
    assert len(policy_items) == 1
    assert package.compression_applied is True
    assert package.metrics.dropped_for_budget >= 1

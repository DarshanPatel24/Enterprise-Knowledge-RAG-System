"""Tests for token estimation, optimization, and context selection."""

from __future__ import annotations

from _assembly_support import ranked_object, ranked_set

from domain.assembly import (
    AssemblyPolicy,
    ContextSelector,
    estimate_tokens,
    optimize_content,
)


def _policy(**overrides: object) -> AssemblyPolicy:
    base: dict[str, object] = {
        "max_context_tokens": 1000,
        "max_objects": 10,
        "ordering": "rank",
        "normalize_whitespace": True,
        "dedupe_content": True,
        "chars_per_token": 4,
        "min_relevance": 0.0,
    }
    base.update(overrides)
    return AssemblyPolicy(**base)  # type: ignore[arg-type]


def test_estimate_tokens_is_deterministic() -> None:
    assert estimate_tokens("", chars_per_token=4) == 0
    assert estimate_tokens("ab", chars_per_token=4) == 1  # non-empty costs >= 1
    assert estimate_tokens("a" * 40, chars_per_token=4) == 10


def test_optimize_collapses_whitespace() -> None:
    assert optimize_content("  a   b\n\tc ", normalize_whitespace=True) == "a b c"


def test_selection_respects_token_budget() -> None:
    objects = [
        ranked_object("d1", "c1", content="a" * 40, composite=0.9, rank=1),
        ranked_object("d2", "c2", content="b" * 40, composite=0.8, rank=2),
    ]
    result = ContextSelector(_policy(max_context_tokens=10)).select(objects)
    assert result.selected[0].ranked.knowledge_object.citation.document_id == "d1"
    assert len(result.selected) == 1
    assert result.dropped_for_budget == 1


def test_selection_dedupes_identical_content() -> None:
    objects = [
        ranked_object("d1", "c1", content="same", composite=0.9, rank=1),
        ranked_object("d2", "c2", content="same", composite=0.8, rank=2),
    ]
    result = ContextSelector(_policy()).select(objects)
    assert len(result.selected) == 1
    assert result.dropped_duplicates == 1


def test_selection_filters_below_relevance() -> None:
    objects = [ranked_object("d1", "c1", content="x", composite=0.1, rank=1)]
    result = ContextSelector(_policy(min_relevance=0.5)).select(objects)
    assert result.selected == ()
    assert result.dropped_below_relevance == 1


def test_max_objects_cap() -> None:
    objects = [
        ranked_object(f"d{i}", "c1", content=f"c{i}", composite=0.9, rank=i + 1)
        for i in range(3)
    ]
    result = ContextSelector(_policy(max_objects=2)).select(objects)
    assert len(result.selected) == 2
    assert result.dropped_for_budget == 1


def test_unused_ranked_set_helper() -> None:
    # ranked_set is exercised by the engine tests; sanity-check it here.
    assert ranked_set().object_count == 0

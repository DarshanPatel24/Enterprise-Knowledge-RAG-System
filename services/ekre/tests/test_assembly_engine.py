"""Tests for the context assembly engine (packaging + citation guarantees)."""

from __future__ import annotations

from _assembly_support import ranked_object, ranked_set

from config.settings import AssemblySettings
from domain.assembly import AssemblyPolicy, ContextAssemblyEngine


def _engine(**overrides: object) -> ContextAssemblyEngine:
    settings = AssemblySettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return ContextAssemblyEngine(AssemblyPolicy.from_settings(settings))


def test_assemble_packages_citation_preserving_candidates() -> None:
    rks = ranked_set(
        ranked_object("d1", "c1", content="alpha", composite=0.9, rank=1),
        ranked_object("d2", "c2", content="beta", composite=0.7, rank=2),
    )
    result = _engine().assemble(rks, query="compare", tenant_id="tenant-a")
    package = result.package
    assert package.query == "compare"
    assert package.tenant_id == "tenant-a"
    assert package.security_filtered is True
    # Citation lineage is never dropped.
    first = package.candidates[0].citation
    assert first.document_id == "d1"
    assert first.chunk_id == "c1"
    assert first.source_path == "/docs/d1.md"
    assert package.candidates[0].relevance_score == 0.9
    assert package.candidates[0].explanation is not None


def test_metrics_report_selection() -> None:
    rks = ranked_set(
        ranked_object("d1", "c1", content="a" * 40, composite=0.9, rank=1),
        ranked_object("d2", "c2", content="b" * 40, composite=0.8, rank=2),
    )
    result = _engine(max_context_tokens=10).assemble(rks, query="q", tenant_id="t")
    assert result.metrics.considered_count == 2
    assert result.metrics.selected_count == 1
    assert result.metrics.dropped_for_budget == 1
    assert result.metrics.token_budget == 10


def test_document_ordering_sorts_by_citation() -> None:
    rks = ranked_set(
        ranked_object("d2", "c1", content="beta", composite=0.9, rank=1),
        ranked_object("d1", "c1", content="alpha", composite=0.8, rank=2),
    )
    result = _engine(ordering="document").assemble(rks, query="q", tenant_id="t")
    ids = [c.citation.document_id for c in result.package.candidates]
    assert ids == ["d1", "d2"]


def test_empty_ranked_set_yields_empty_package() -> None:
    result = _engine().assemble(ranked_set(), query="q", tenant_id="t")
    assert result.package.candidates == []
    assert result.metrics.selected_count == 0

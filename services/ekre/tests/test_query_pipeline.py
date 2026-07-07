"""Tests for the Query Intelligence pipeline orchestrator."""

from __future__ import annotations

from composition import build_query_intelligence_engine
from config.settings import EkreSettings
from domain.query import RetrievalIntent


def _engine() -> object:
    return build_query_intelligence_engine(EkreSettings(_env_file=None))


def test_pipeline_produces_structured_query() -> None:
    result = _engine().analyze("compare EKIE and EKRE", tenant_id="tenant-a")
    assert result.tenant_id == "tenant-a"
    assert result.intent.intent is RetrievalIntent.COMPARISON
    assert result.plan.steps
    stages = {t.stage for t in result.transformations}
    assert {"understanding", "intent", "enrichment", "planning"} <= stages


def test_pipeline_is_deterministic() -> None:
    engine = _engine()
    first = engine.analyze("compare EKIE and EKRE", tenant_id="t", query_id="fixed")
    second = engine.analyze("compare EKIE and EKRE", tenant_id="t", query_id="fixed")
    assert first == second


def test_pipeline_understanding_is_deterministic_source_by_default() -> None:
    result = _engine().analyze("travel guide", tenant_id="t")
    assert result.understanding.source == "deterministic"

"""Tests for the retrieval execution trace builder."""

from __future__ import annotations

from domain.governance import build_retrieval_trace
from domain.observability import LatencyBreakdown


def test_trace_reports_stages_and_total() -> None:
    breakdown = LatencyBreakdown(
        stages={"query_understanding": 5.0, "execution": 40.0}, total_ms=45.0
    )
    trace = build_retrieval_trace(
        breakdown,
        execution_id="exec-1",
        trace_id="trace-1",
        tenant_id="tenant-a",
        budget_ms=500.0,
    )
    assert {s.stage for s in trace.stages} == {"query_understanding", "execution"}
    assert trace.total_ms == 45.0
    assert trace.over_budget is False


def test_trace_flags_over_budget() -> None:
    breakdown = LatencyBreakdown(stages={"execution": 600.0}, total_ms=600.0)
    trace = build_retrieval_trace(
        breakdown,
        execution_id="exec-1",
        trace_id="trace-1",
        tenant_id="tenant-a",
        budget_ms=500.0,
        redactions=3,
    )
    assert trace.over_budget is True
    assert trace.redactions == 3

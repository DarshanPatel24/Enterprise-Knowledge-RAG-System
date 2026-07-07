"""Tests for observability context binding and latency measurement."""

from __future__ import annotations

from domain.observability import (
    LatencyRecorder,
    correlation_scope,
    get_correlation_id,
    get_query_id,
    get_tenant_id,
)


def test_correlation_scope_binds_and_resets() -> None:
    assert get_tenant_id() is None
    with correlation_scope(tenant_id="t1", correlation_id="c1", query_id="q1"):
        assert get_tenant_id() == "t1"
        assert get_correlation_id() == "c1"
        assert get_query_id() == "q1"
    assert get_tenant_id() is None
    assert get_correlation_id() is None
    assert get_query_id() is None


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_latency_recorder_accumulates_stages() -> None:
    clock = _FakeClock()
    recorder = LatencyRecorder(clock=clock)

    with recorder.stage("vector"):
        clock.advance(0.150)
    with recorder.stage("ranking"):
        clock.advance(0.100)

    breakdown = recorder.breakdown()
    assert breakdown.stages["vector"] == 150.0
    assert breakdown.stages["ranking"] == 100.0
    assert breakdown.total_ms == 250.0


def test_latency_breakdown_flags_over_budget() -> None:
    clock = _FakeClock()
    recorder = LatencyRecorder(clock=clock)
    with recorder.stage("vector"):
        clock.advance(0.200)

    breakdown = recorder.breakdown()
    breaches = breakdown.over_budget({"vector": 150.0, "total": 500.0})
    assert breaches == {"vector": 200.0}

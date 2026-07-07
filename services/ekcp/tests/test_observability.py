"""Tests for the EKCP observability baseline: context scope and latency."""

from __future__ import annotations

from domain.observability import (
    LatencyRecorder,
    correlation_scope,
    get_correlation_id,
    get_session_id,
    get_tenant_id,
)


def test_correlation_scope_binds_and_resets() -> None:
    assert get_tenant_id() is None
    with correlation_scope(tenant_id="t1", correlation_id="c1", session_id="s1"):
        assert get_tenant_id() == "t1"
        assert get_correlation_id() == "c1"
        assert get_session_id() == "s1"
    assert get_tenant_id() is None
    assert get_correlation_id() is None
    assert get_session_id() is None


class _FakeClock:
    """Deterministic clock that advances by a fixed step on each read."""

    def __init__(self, *, step: float) -> None:
        self._now = 0.0
        self._step = step

    def __call__(self) -> float:
        value = self._now
        self._now += self._step
        return value


def test_latency_recorder_measures_stage() -> None:
    clock = _FakeClock(step=0.5)  # 0.5s elapsed per stage -> 500ms
    recorder = LatencyRecorder(clock=clock)
    with recorder.stage("security_gate"):
        pass
    breakdown = recorder.breakdown()
    assert breakdown.stages["security_gate"] == 500.0
    assert breakdown.total_ms == 500.0


def test_latency_over_budget() -> None:
    recorder = LatencyRecorder()
    recorder.record("gate", 120.0)
    breakdown = recorder.breakdown()
    breaches = breakdown.over_budget({"gate": 100.0, "total": 50.0})
    assert breaches["gate"] == 120.0
    assert breaches["total"] == 120.0

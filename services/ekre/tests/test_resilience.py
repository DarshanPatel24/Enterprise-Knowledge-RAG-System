"""Tests for the circuit breaker and multi-tenant limiter."""

from __future__ import annotations

from domain.resilience import CircuitBreaker, CircuitState, TenantConcurrencyLimiter


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_breaker_trips_open_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout_seconds=10.0)
    for _ in range(3):
        breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    assert breaker.allow() is False


def test_breaker_half_opens_after_reset_then_closes_on_success() -> None:
    clock = _FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout_seconds=5.0, clock=clock)
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    clock.advance(5.0)
    assert breaker.state is CircuitState.HALF_OPEN
    assert breaker.allow() is True
    breaker.record_success()
    assert breaker.state is CircuitState.CLOSED


def test_success_resets_failure_count() -> None:
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout_seconds=5.0)
    breaker.record_failure()
    breaker.record_success()
    breaker.record_failure()
    assert breaker.state is CircuitState.CLOSED


def test_tenant_limiter_admits_up_to_ceiling() -> None:
    limiter = TenantConcurrencyLimiter(2)
    assert limiter.acquire("t1") is True
    assert limiter.acquire("t1") is True
    assert limiter.acquire("t1") is False  # ceiling reached
    limiter.release("t1")
    assert limiter.acquire("t1") is True
    # Other tenants are independent.
    assert limiter.acquire("t2") is True


def test_tenant_limiter_unlimited_when_zero() -> None:
    limiter = TenantConcurrencyLimiter(0)
    assert all(limiter.acquire("t1") for _ in range(100))


def test_tenant_limiter_slot_context_manager() -> None:
    limiter = TenantConcurrencyLimiter(1)
    with limiter.slot("t1") as admitted:
        assert admitted is True
        assert limiter.acquire("t1") is False
    assert limiter.active("t1") == 0

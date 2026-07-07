"""Circuit breaker for fault isolation (handbook Chapter 30.7).

A deterministic circuit-breaker state machine that isolates a repeatedly failing
dependency (worker or connector) so it never becomes a platform bottleneck. It
complements the pipeline's existing graceful degradation. Deterministic under an
injected clock.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from time import monotonic


class CircuitState(StrEnum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Trips open after consecutive failures; probes after a reset timeout."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        reset_timeout_seconds: float = 30.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._reset_timeout_seconds = reset_timeout_seconds
        self._clock = clock
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at = 0.0

    @property
    def state(self) -> CircuitState:
        """Return the current state, transitioning OPEN -> HALF_OPEN on timeout."""
        if self._state is CircuitState.OPEN and (
            self._clock() - self._opened_at >= self._reset_timeout_seconds
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    def allow(self) -> bool:
        """Return whether a call may proceed under the current state."""
        return self.state is not CircuitState.OPEN

    def record_success(self) -> None:
        """Record a success: reset failures and close the circuit."""
        self._failures = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failure: trip open once the threshold is reached."""
        self._failures += 1
        if self._failures >= self._failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = self._clock()

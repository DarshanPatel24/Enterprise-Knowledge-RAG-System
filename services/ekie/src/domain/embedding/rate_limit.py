"""Token-bucket rate limiter for paced ingestion (per-minute throughput caps).

Used to honor optional per-minute limits when embedding chunks or upserting
vectors. A limit of ``0`` (or negative) disables limiting, so the default
behavior is unchanged. The clock and sleep callables are injectable to keep the
limiter deterministic under test (mirrors :func:`run_with_retry`).
"""

from __future__ import annotations

import time
from collections.abc import Callable


class RateLimiter:
    """Paces work to at most ``max_per_minute`` units using a token bucket.

    The bucket starts full, allowing an initial burst of up to
    ``max_per_minute`` units, then refills continuously at ``max_per_minute``
    units per minute. ``acquire`` blocks only when the bucket is empty.
    """

    def __init__(
        self,
        max_per_minute: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._rate_per_second = max_per_minute / 60.0 if max_per_minute > 0 else 0.0
        self._capacity = float(max_per_minute) if max_per_minute > 0 else 0.0
        self._tokens = self._capacity
        self._clock = clock
        self._sleep = sleep
        self._last = clock()

    @property
    def enabled(self) -> bool:
        """Return True when the limiter enforces a positive per-minute rate."""
        return self._rate_per_second > 0.0

    def acquire(self, units: int = 1) -> float:
        """Block until ``units`` tokens are available; return seconds waited."""
        if not self.enabled or units <= 0:
            return 0.0
        self._refill()
        waited = 0.0
        if self._tokens < units:
            deficit = units - self._tokens
            waited = deficit / self._rate_per_second
            self._sleep(waited)
            self._refill()
        self._tokens -= units
        return waited

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._last
        if elapsed <= 0.0:
            return
        self._last = now
        self._tokens = min(
            self._capacity, self._tokens + elapsed * self._rate_per_second
        )

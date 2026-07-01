"""Retry with exponential backoff for recoverable synchronization failures.

Connector operations (discovery, byte reads) can fail transiently. This helper
retries them so a synchronization failure does not corrupt the Digital Twin,
per EKIE handbook Chapter 6.20. The sleep function is injectable to keep tests
fast and deterministic.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for retry attempts and backoff timing."""

    max_attempts: int = 3
    backoff_base_seconds: float = 0.5
    backoff_multiplier: float = 2.0


def run_with_retry(
    operation: Callable[[], T],
    *,
    policy: RetryPolicy,
    retryable: type[Exception] | tuple[type[Exception], ...] = Exception,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run ``operation``, retrying on ``retryable`` errors using backoff.

    Raises the last exception if all attempts fail.
    """
    if policy.max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last_error: Exception | None = None
    for attempt in range(policy.max_attempts):
        try:
            return operation()
        except retryable as exc:
            last_error = exc
            if attempt == policy.max_attempts - 1:
                break
            delay = policy.backoff_base_seconds * (policy.backoff_multiplier**attempt)
            sleep(delay)

    if last_error is None:  # pragma: no cover - defensive; loop always sets it
        raise RuntimeError("retry loop exhausted without capturing an error")
    raise last_error

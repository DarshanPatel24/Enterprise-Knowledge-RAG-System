"""Retry with exponential backoff for transient provider failures (handbook 10.13).

Embedding provider calls can fail transiently (timeouts, rate limits). This
helper retries them under a configurable attempt budget. The sleep function is
injectable to keep tests fast and deterministic.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

_T = TypeVar("_T")


def run_with_retry(
    operation: Callable[[], _T],
    *,
    max_retries: int,
    retryable: type[Exception] | tuple[type[Exception], ...] = Exception,
    backoff_base_seconds: float = 0.5,
    backoff_multiplier: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> _T:
    """Run ``operation``, retrying on ``retryable`` errors using backoff.

    ``max_retries`` is the number of additional attempts after the first, so the
    total attempt count is ``max_retries + 1``. Raises the last error if all
    attempts fail.
    """
    if max_retries < 0:
        raise ValueError("max_retries must be zero or greater")

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except retryable as exc:
            last_error = exc
            if attempt == max_retries:
                break
            sleep(backoff_base_seconds * (backoff_multiplier**attempt))

    if last_error is None:  # pragma: no cover - defensive; loop always sets it
        raise RuntimeError("retry loop exhausted without capturing an error")
    raise last_error

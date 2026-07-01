"""Token estimation and batching helpers (handbook 10.10-10.11)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TypeVar

_T = TypeVar("_T")


def estimate_tokens(text: str) -> int:
    """Return an approximate whitespace token count for ``text``.

    Deterministic and provider-independent so token validation and cost
    estimation are reproducible across runs.
    """
    return len(text.split())


def estimate_cost(token_count: int, cost_per_1k_tokens: float) -> float:
    """Return the deterministic estimated cost for ``token_count`` tokens."""
    return round(token_count / 1000.0 * cost_per_1k_tokens, 6)


def batched(items: list[_T], size: int) -> Iterator[list[_T]]:
    """Yield consecutive batches of at most ``size`` items (handbook 10.11)."""
    if size <= 0:
        raise ValueError("batch size must be a positive integer")
    for start in range(0, len(items), size):
        yield items[start : start + size]

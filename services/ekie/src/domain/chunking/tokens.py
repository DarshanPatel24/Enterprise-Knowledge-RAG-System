"""Deterministic token estimation for chunk budget management (handbook 9.14)."""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Return an approximate whitespace token count for ``text``.

    The estimate is intentionally deterministic and provider-independent so that
    chunk identity remains stable across embedding models (ADR-019).
    """
    return len(text.split())

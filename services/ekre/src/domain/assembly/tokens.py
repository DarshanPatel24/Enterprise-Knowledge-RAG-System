"""Token estimation and content optimization (handbook Chapter 26.10).

Deterministic, dependency-free helpers: a coarse character-based token estimate
(no model tokenizer on the offline path) and content optimization (whitespace
normalization) that must preserve factual accuracy.
"""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def estimate_tokens(text: str, *, chars_per_token: int) -> int:
    """Return a coarse token estimate for ``text``.

    Uses a character-per-token ratio so the estimate is deterministic and does
    not require a model tokenizer. Non-empty text always costs at least 1 token.
    """
    if not text:
        return 0
    return max(1, len(text) // chars_per_token)


def optimize_content(text: str, *, normalize_whitespace: bool) -> str:
    """Return content optimized for the context window without altering facts."""
    optimized = text.strip()
    if normalize_whitespace:
        optimized = _WHITESPACE.sub(" ", optimized)
    return optimized

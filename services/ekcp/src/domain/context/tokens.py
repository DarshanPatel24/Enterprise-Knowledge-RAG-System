"""Deterministic token estimation for context and prompt budgeting.

Uses a character-per-token heuristic so budgeting is reproducible offline
without a model tokenizer. The real tokenizer is a model-gateway concern (S3);
this estimate governs assembly and prompt construction budgets.
"""

from __future__ import annotations


def estimate_tokens(text: str, *, chars_per_token: int = 4) -> int:
    """Estimate the token count of ``text`` (minimum 1 for non-empty input)."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // max(1, chars_per_token))

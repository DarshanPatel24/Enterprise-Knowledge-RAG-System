"""Passage truncation for the cross-encoder reranker."""

from __future__ import annotations

# Passages are truncated before scoring to bound the reranker model input size.
MAX_PASSAGE_CHARS = 800


def truncate_passage(text: str) -> str:
    """Return the passage truncated to the maximum prompt length."""
    if len(text) <= MAX_PASSAGE_CHARS:
        return text
    return text[:MAX_PASSAGE_CHARS]

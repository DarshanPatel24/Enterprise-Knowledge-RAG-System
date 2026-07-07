"""Prompt template for the optional LLM reranker."""

from __future__ import annotations

RERANK_SYSTEM_PROMPT = (
    "You are a deterministic reranking assistant for an enterprise retrieval "
    "system. Given a query and a list of candidate passages, return the candidate "
    "ids ordered from most to least relevant to the query. Use only the provided "
    "passages; never invent ids. Respond only in the requested structured format."
)

RERANK_HUMAN_TEMPLATE = "Query:\n{query}\n\nCandidates:\n{candidates}\n\n{format_instructions}"

# Passages are truncated before prompting to bound token usage.
MAX_PASSAGE_CHARS = 800


def truncate_passage(text: str) -> str:
    """Return the passage truncated to the maximum prompt length."""
    if len(text) <= MAX_PASSAGE_CHARS:
        return text
    return text[:MAX_PASSAGE_CHARS]

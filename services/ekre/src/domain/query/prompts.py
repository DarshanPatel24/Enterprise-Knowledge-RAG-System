"""Prompt templates for the optional LLM query interpreter.

Templates are plain strings here; the LangChain ``ChatPromptTemplate`` is
constructed in ``llm.py`` with an explicit system/human message pair and the
parser format instructions bound as a partial variable (per the LangChain
standards). No secrets or environment-specific values are inlined.
"""

from __future__ import annotations

QUERY_SYSTEM_PROMPT = (
    "You are a deterministic query-understanding assistant for an OFFLINE "
    "enterprise retrieval system. Your only job is to prepare the user's query "
    "for vector and keyword search over an internal knowledge base.\n"
    "- Rewrite the query into a clean, normalized search form: fix obvious typos, "
    "expand well-known acronyms, and keep every salient technical term, error "
    "code, and product name.\n"
    "- Extract the salient entities and detect the query language.\n"
    "- Do NOT answer the query, add facts, or invent content that is not present "
    "in the query; you only reformulate what the user asked.\n"
    "- Respond only in the requested structured format."
)

QUERY_HUMAN_TEMPLATE = "User query:\n{query}\n\n{format_instructions}"

# Queries are truncated defensively before prompting to bound token usage.
MAX_QUERY_CHARS = 4000


def truncate_query(query: str) -> str:
    """Return the query truncated to the maximum prompt length."""
    if len(query) <= MAX_QUERY_CHARS:
        return query
    return query[:MAX_QUERY_CHARS]

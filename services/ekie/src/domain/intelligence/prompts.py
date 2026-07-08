"""Prompt text for optional LLM-based document intelligence (handbook 8.11).

Prompt templates are kept as plain strings here so this module stays free of any
LangChain dependency. The optional :class:`~domain.intelligence.analyzers.llm.LlmAnalyzer`
assembles them into a ``ChatPromptTemplate`` only when LLM analysis is enabled.
"""

from __future__ import annotations

# Upper bound on document text sent to the model. Bounds prompt size and cost
# while remaining large enough to capture a document's dominant subject.
MAX_DOCUMENT_CHARS = 6000

TOPIC_SYSTEM_PROMPT = (
    "You are a precise document analyst for an OFFLINE enterprise knowledge base. "
    "Using ONLY the document text provided, identify its single dominant subject. "
    "Do not use outside knowledge or infer beyond the text. "
    "Respond with a concise topic of at most eight words. "
    "Return only the topic text, with no punctuation, labels, or explanation."
)

TOPIC_USER_TEMPLATE = "Document:\n{document}\n\nPrimary topic:"


def truncate_document(text: str) -> str:
    """Return ``text`` bounded to :data:`MAX_DOCUMENT_CHARS` characters."""
    if len(text) <= MAX_DOCUMENT_CHARS:
        return text
    return text[:MAX_DOCUMENT_CHARS]

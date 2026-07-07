"""Citation builder (handbook Chapter 26.11).

Converts a selected ranked object into a citation-preserving retrieval candidate.
The citation lineage (document_id, chunk_id, source_path) is carried verbatim
from the knowledge object and must never be dropped; the ranking explanation is
preserved so the downstream response can attribute and explain every source.
"""

from __future__ import annotations

from contracts.retrieval import RetrievalCandidate
from domain.assembly.errors import AssemblyError, AssemblyErrorType
from domain.assembly.selection import SelectedContext


def to_candidate(selected: SelectedContext) -> RetrievalCandidate:
    """Build a citation-preserving candidate from a selected ranked object."""
    citation = selected.ranked.knowledge_object.citation
    if not (citation.document_id and citation.chunk_id and citation.source_path):
        raise AssemblyError(
            AssemblyErrorType.CITATION_DROPPED,
            "citation lineage must be preserved through assembly",
        )
    score = max(0.0, min(1.0, selected.ranked.composite_score))
    return RetrievalCandidate(
        citation=citation,
        content=selected.content or selected.ranked.knowledge_object.content,
        relevance_score=score,
        explanation=selected.ranked.explanation or None,
    )

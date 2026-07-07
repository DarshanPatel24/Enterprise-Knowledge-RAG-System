"""Normalize repository documents into standardized retrieval candidates."""

from __future__ import annotations

from collections.abc import Sequence

from contracts.retrieval import Citation, RetrievalCandidate
from domain.connectors.base import RepositoryDocument


def to_candidates(
    documents: Sequence[RepositoryDocument], *, explanation: str
) -> tuple[RetrievalCandidate, ...]:
    """Convert repository documents into citation-preserving candidates."""
    return tuple(
        RetrievalCandidate(
            citation=Citation(
                document_id=doc.document_id,
                chunk_id=doc.chunk_id,
                source_path=doc.source_path or f"/{doc.document_id}",
            ),
            content=doc.content,
            relevance_score=max(0.0, min(1.0, doc.score)),
            explanation=explanation,
        )
        for doc in documents
    )

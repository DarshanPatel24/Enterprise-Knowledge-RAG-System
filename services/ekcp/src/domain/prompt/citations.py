"""Citation-readiness validation for incoming retrieval context.

Enforces the handbook rule: any retrieved chunk missing a complete citation
(``source_path``, ``document_id``, ``chunk_id``) or content must be stripped
before prompt generation to prevent hallucinated citations. The validator is
pure and deterministic; it never mutates the input package.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from contracts.retrieval import RetrievalCandidate, RetrievalContextPackage


class CitationReadinessReport(BaseModel):
    """Immutable outcome of citation-readiness validation."""

    model_config = ConfigDict(frozen=True)

    total: int
    ready: int
    dropped: int
    dropped_reasons: tuple[str, ...] = ()

    @property
    def all_ready(self) -> bool:
        """Return whether every candidate was citation-ready."""
        return self.dropped == 0


def _is_ready(candidate: RetrievalCandidate) -> tuple[bool, str]:
    citation = candidate.citation
    if not candidate.content.strip():
        return False, "empty content"
    if not citation.source_path.strip():
        return False, "missing source_path"
    if not citation.document_id.strip():
        return False, "missing document_id"
    if not citation.chunk_id.strip():
        return False, "missing chunk_id"
    return True, ""


def validate_citation_readiness(
    package: RetrievalContextPackage,
) -> tuple[tuple[RetrievalCandidate, ...], CitationReadinessReport]:
    """Return the citation-ready candidates and a readiness report."""
    ready: list[RetrievalCandidate] = []
    reasons: list[str] = []
    for candidate in package.candidates:
        ok, reason = _is_ready(candidate)
        if ok:
            ready.append(candidate)
        else:
            reasons.append(reason)
    report = CitationReadinessReport(
        total=len(package.candidates),
        ready=len(ready),
        dropped=len(reasons),
        dropped_reasons=tuple(reasons),
    )
    return tuple(ready), report

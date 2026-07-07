"""Unified Candidate Collection Framework (handbook Chapter 23).

Collects candidates produced by independent retrieval workers into a single,
deterministic, immutable Unified Candidate Set, validating required fields and
recording per-source provenance. It performs no deduplication, ranking, or
fusion --- those belong to later stages.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from domain.execution.models import WorkerOutcome
from domain.fusion.models import CollectedCandidate, UnifiedCandidateSet

# Deterministic worker/source ordering when candidates are collected.
_ENGINE_ORDER = {"vector": 0, "keyword": 1, "metadata": 2}


class CandidateCollector:
    """Aggregates worker outcomes into a Unified Candidate Set."""

    def collect(self, outcomes: Sequence[WorkerOutcome]) -> UnifiedCandidateSet:
        """Collect candidates from successful worker outcomes into a UCS."""
        collected: list[CollectedCandidate] = []
        source_counts: dict[str, int] = {}
        warnings: list[str] = []

        for outcome in outcomes:
            if not outcome.succeeded:
                continue
            for rank, candidate in enumerate(outcome.candidates):
                citation = candidate.citation
                if not citation.document_id or not citation.chunk_id:
                    warnings.append(
                        f"rejected malformed candidate from {outcome.worker_id!r}"
                    )
                    continue
                collected.append(
                    CollectedCandidate(
                        candidate=candidate,
                        worker_id=outcome.worker_id,
                        engine=outcome.engine,
                        rank=rank,
                        score=candidate.relevance_score,
                    )
                )
                source_counts[outcome.engine.value] = (
                    source_counts.get(outcome.engine.value, 0) + 1
                )

        collected.sort(key=_collection_key)
        return UnifiedCandidateSet(
            collection_id=f"ucs-{uuid.uuid4().hex[:12]}",
            candidates=tuple(collected),
            source_counts=source_counts,
            total=len(collected),
            warnings=tuple(warnings),
        )


def _collection_key(item: CollectedCandidate) -> tuple[int, int, str, str]:
    return (
        _ENGINE_ORDER.get(item.engine.value, 99),
        item.rank,
        item.candidate.citation.document_id,
        item.candidate.citation.chunk_id,
    )

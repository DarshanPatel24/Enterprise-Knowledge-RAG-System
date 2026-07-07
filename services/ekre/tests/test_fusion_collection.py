"""Tests for the Unified Candidate Collection Framework."""

from __future__ import annotations

from _fusion_support import candidate, outcome

from domain.execution import WorkerState
from domain.fusion import CandidateCollector
from domain.query.models import RetrievalEngineType


def test_collect_records_provenance_and_counts() -> None:
    ucs = CandidateCollector().collect(
        [
            outcome(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]),
            outcome(
                RetrievalEngineType.KEYWORD,
                [candidate("d1", "c1", 0.7), candidate("d2", "c2", 0.6)],
            ),
        ]
    )
    assert ucs.total == 3
    assert ucs.source_counts == {"vector": 1, "keyword": 2}
    # Provenance: rank is the position within the producing worker's list.
    keyword_ranks = sorted(
        c.rank for c in ucs.candidates if c.engine is RetrievalEngineType.KEYWORD
    )
    assert keyword_ranks == [0, 1]


def test_failed_outcomes_are_skipped() -> None:
    ucs = CandidateCollector().collect(
        [
            outcome(
                RetrievalEngineType.VECTOR,
                [candidate("d1", "c1", 0.9)],
                state=WorkerState.FAILED,
            ),
            outcome(RetrievalEngineType.KEYWORD, [candidate("d2", "c2", 0.6)]),
        ]
    )
    assert ucs.total == 1
    assert ucs.candidates[0].engine is RetrievalEngineType.KEYWORD


def test_collection_is_deterministic() -> None:
    outcomes = [
        outcome(RetrievalEngineType.KEYWORD, [candidate("d2", "c2", 0.6)]),
        outcome(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]),
    ]
    first = CandidateCollector().collect(outcomes)
    second = CandidateCollector().collect(outcomes)
    assert [c.candidate.citation.document_id for c in first.candidates] == [
        c.candidate.citation.document_id for c in second.candidates
    ]
    # Vector sorts before keyword regardless of input order.
    assert first.candidates[0].engine is RetrievalEngineType.VECTOR

"""Tests for the Candidate Fusion Framework (RRF, identity, provenance)."""

from __future__ import annotations

from _fusion_support import candidate, outcome

from domain.fusion import CandidateCollector, CandidateFusion, FusionPolicy
from domain.query.models import RetrievalEngineType


def _fuse(outcomes: list, policy: FusionPolicy = FusionPolicy.CHUNK_IDENTITY) -> object:
    ucs = CandidateCollector().collect(outcomes)
    return CandidateFusion(policy, rrf_k=60).fuse(ucs)


def test_same_asset_fuses_into_one_object_with_all_evidence() -> None:
    fks = _fuse(
        [
            outcome(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]),
            outcome(RetrievalEngineType.KEYWORD, [candidate("d1", "c1", 0.7)]),
        ]
    )
    assert fks.object_count == 1
    obj = fks.objects[0]
    assert len(obj.evidence) == 2
    assert set(obj.source_engines) == {
        RetrievalEngineType.VECTOR,
        RetrievalEngineType.KEYWORD,
    }
    # Two rank-0 observations: RRF = 2 * 1/(60+0+1).
    assert abs(obj.fusion_score - 2.0 / 61.0) < 1e-9
    assert obj.best_score == 0.9


def test_distinct_chunks_stay_separate() -> None:
    fks = _fuse(
        [
            outcome(
                RetrievalEngineType.VECTOR,
                [candidate("d1", "c1", 0.9), candidate("d1", "c2", 0.8)],
            )
        ]
    )
    assert fks.object_count == 2


def test_document_policy_groups_chunks() -> None:
    fks = _fuse(
        [
            outcome(
                RetrievalEngineType.VECTOR,
                [candidate("d1", "c1", 0.9), candidate("d1", "c2", 0.8)],
            )
        ],
        policy=FusionPolicy.DOCUMENT_IDENTITY,
    )
    assert fks.object_count == 1
    assert fks.objects[0].knowledge_id == "ko-d1"


def test_more_evidence_ranks_higher_by_fusion_score() -> None:
    fks = _fuse(
        [
            outcome(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.5)]),
            outcome(RetrievalEngineType.KEYWORD, [candidate("d1", "c1", 0.5)]),
            outcome(RetrievalEngineType.METADATA, [candidate("d2", "c2", 0.95)]),
        ]
    )
    # d1 has two rank-0 sources -> higher RRF than the single-source d2.
    assert fks.objects[0].citation.document_id == "d1"


def test_fusion_is_deterministic() -> None:
    outcomes = [
        outcome(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]),
        outcome(RetrievalEngineType.KEYWORD, [candidate("d1", "c1", 0.7)]),
    ]
    # fusion_id is a fresh UUID per call; the fused objects are deterministic.
    assert _fuse(outcomes).objects == _fuse(outcomes).objects

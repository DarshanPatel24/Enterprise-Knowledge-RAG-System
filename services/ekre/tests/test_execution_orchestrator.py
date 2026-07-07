"""Tests for the retrieval orchestrator (collection, status, degradation)."""

from __future__ import annotations

import pytest
from _execution_support import FailingWorker, candidate, plan, static_worker

from composition import build_retrieval_orchestrator
from config.settings import EkreSettings
from domain.execution import (
    ExecutionError,
    ExecutionStatus,
    WorkerRegistry,
)
from domain.query.models import RetrievalEngineType


def _orchestrator(registry: WorkerRegistry, *, fail_open: bool = True) -> object:
    settings = EkreSettings(_env_file=None)
    settings = settings.model_copy(
        update={"execution": settings.execution.model_copy(update={"fail_open": fail_open})}
    )
    return build_retrieval_orchestrator(settings, registry=registry)


def test_all_workers_succeed_completed() -> None:
    registry = WorkerRegistry()
    registry.register(static_worker(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]))
    registry.register(static_worker(RetrievalEngineType.KEYWORD, [candidate("d2", "c2", 0.7)]))
    session = _orchestrator(registry).execute(
        plan(RetrievalEngineType.VECTOR, RetrievalEngineType.KEYWORD),
        tenant_id="tenant-a",
    )
    assert session.status is ExecutionStatus.COMPLETED
    assert session.degraded is False
    assert session.candidate_count == 2
    # Deterministic: highest score first.
    assert session.candidates[0].relevance_score == 0.9


def test_partial_failure_is_isolated() -> None:
    registry = WorkerRegistry()
    registry.register(static_worker(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.9)]))
    registry.register(FailingWorker(RetrievalEngineType.KEYWORD))
    session = _orchestrator(registry).execute(
        plan(RetrievalEngineType.VECTOR, RetrievalEngineType.KEYWORD),
        tenant_id="tenant-a",
    )
    assert session.status is ExecutionStatus.PARTIAL
    assert session.degraded is True
    assert session.succeeded_count == 1
    assert session.failed_count == 1
    assert session.candidate_count == 1


def test_all_fail_returns_failed_session_when_fail_open() -> None:
    registry = WorkerRegistry()
    registry.register(FailingWorker(RetrievalEngineType.VECTOR))
    session = _orchestrator(registry, fail_open=True).execute(
        plan(RetrievalEngineType.VECTOR), tenant_id="tenant-a"
    )
    assert session.status is ExecutionStatus.FAILED
    assert session.candidate_count == 0


def test_all_fail_raises_when_not_fail_open() -> None:
    registry = WorkerRegistry()
    registry.register(FailingWorker(RetrievalEngineType.VECTOR))
    with pytest.raises(ExecutionError):
        _orchestrator(registry, fail_open=False).execute(
            plan(RetrievalEngineType.VECTOR), tenant_id="tenant-a"
        )


def test_candidate_deduplication_keeps_highest_score() -> None:
    registry = WorkerRegistry()
    registry.register(static_worker(RetrievalEngineType.VECTOR, [candidate("d1", "c1", 0.6)]))
    registry.register(static_worker(RetrievalEngineType.KEYWORD, [candidate("d1", "c1", 0.95)]))
    session = _orchestrator(registry).execute(
        plan(RetrievalEngineType.VECTOR, RetrievalEngineType.KEYWORD),
        tenant_id="tenant-a",
    )
    assert session.candidate_count == 1
    assert session.candidates[0].relevance_score == 0.95

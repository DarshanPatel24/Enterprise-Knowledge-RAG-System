"""Tests for knowledge integration: circuit breaker, retriever, degradation."""

from __future__ import annotations

from config.settings import KnowledgeSettings
from contracts.retrieval import (
    Citation,
    RetrievalCandidate,
    RetrievalContextPackage,
)
from domain.knowledge import (
    CircuitBreaker,
    CircuitState,
    KnowledgeClient,
    KnowledgeError,
    KnowledgeErrorType,
    KnowledgePolicy,
    KnowledgeRetriever,
)


class _FakeClock:
    def __init__(self) -> None:
        self._now = 0.0

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class _OkClient(KnowledgeClient):
    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str,
        security_context: dict[str, str],
        correlation_id: str | None = None,
    ) -> RetrievalContextPackage:
        return RetrievalContextPackage(
            query=query,
            tenant_id=tenant_id,
            candidates=[
                RetrievalCandidate(
                    citation=Citation(
                        document_id="d1", chunk_id="c1", source_path="/docs/a.md"
                    ),
                    content="enterprise evidence",
                    relevance_score=0.9,
                )
            ],
        )


class _FailingClient(KnowledgeClient):
    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str,
        security_context: dict[str, str],
        correlation_id: str | None = None,
    ) -> RetrievalContextPackage:
        raise KnowledgeError(KnowledgeErrorType.BACKPRESSURE, "429")


def _policy(**overrides: object) -> KnowledgePolicy:
    return KnowledgePolicy.from_settings(
        KnowledgeSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    )


_SEC = {"user_id": "u1", "tenant_id": "tenant-a", "classification_clearance": "internal"}


def test_circuit_breaker_trips_and_recovers() -> None:
    clock = _FakeClock()
    breaker = CircuitBreaker(
        failure_threshold=2, reset_timeout_seconds=30.0, clock=clock
    )
    assert breaker.allow()
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    assert not breaker.allow()
    clock.advance(31.0)
    assert breaker.state is CircuitState.HALF_OPEN
    breaker.record_success()
    assert breaker.state is CircuitState.CLOSED


def test_retriever_disabled_degrades() -> None:
    retriever = KnowledgeRetriever(_policy(enabled=False))
    result = retriever.retrieve(
        "policy", tenant_id="tenant-a", security_context=_SEC
    )
    assert result.degraded is True
    assert result.reason == "knowledge_disabled"
    assert result.package is None


def test_retriever_success() -> None:
    retriever = KnowledgeRetriever(_policy(enabled=True), client=_OkClient())
    result = retriever.retrieve(
        "remote work policy", tenant_id="tenant-a", security_context=_SEC
    )
    assert result.degraded is False
    assert result.has_knowledge is True
    assert result.candidate_count == 1


def test_retriever_degrades_on_client_failure() -> None:
    retriever = KnowledgeRetriever(_policy(enabled=True), client=_FailingClient())
    result = retriever.retrieve(
        "policy", tenant_id="tenant-a", security_context=_SEC
    )
    assert result.degraded is True
    assert result.reason == "backpressure"


def test_retriever_degrades_when_circuit_open() -> None:
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout_seconds=60.0)
    breaker.record_failure()  # trips open
    retriever = KnowledgeRetriever(
        _policy(enabled=True), client=_OkClient(), circuit_breaker=breaker
    )
    result = retriever.retrieve(
        "policy", tenant_id="tenant-a", security_context=_SEC
    )
    assert result.degraded is True
    assert result.reason == "circuit_open"

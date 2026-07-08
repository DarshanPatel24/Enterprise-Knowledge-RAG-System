"""Knowledge retriever: resilient EKRE consumption with graceful degradation.

Wraps the EKRE client in a circuit breaker and returns a :class:`KnowledgeResult`
that either carries the retrieved package or signals degradation so the caller
falls back to local memory. The session never fails because EKRE is unavailable;
backpressure, timeouts, and an open circuit all degrade gracefully.
"""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from domain.knowledge.circuit_breaker import CircuitBreaker
from domain.knowledge.client import KnowledgeClient
from domain.knowledge.errors import KnowledgeError
from domain.knowledge.models import KnowledgeResult
from domain.knowledge.policy import KnowledgePolicy
from domain.observability import get_logger

logger = get_logger("ekcp.knowledge")


class KnowledgeRetriever:
    """Retrieve enterprise knowledge from EKRE, degrading to local memory on failure."""

    def __init__(
        self,
        policy: KnowledgePolicy,
        *,
        client: KnowledgeClient | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        self._policy = policy
        self._client = client
        self._breaker = circuit_breaker or CircuitBreaker(
            failure_threshold=policy.circuit_breaker_threshold,
            reset_timeout_seconds=policy.circuit_breaker_reset_seconds,
        )
        self._clock = clock

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """Return the circuit breaker guarding the EKRE dependency."""
        return self._breaker

    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str,
        security_context: dict[str, str],
        correlation_id: str | None = None,
    ) -> KnowledgeResult:
        """Retrieve knowledge, returning a degradation result when EKRE is unavailable."""
        if not self._policy.enabled or self._client is None:
            return KnowledgeResult(degraded=True, reason="knowledge_disabled")
        if not self._breaker.allow():
            logger.warning("knowledge_circuit_open", extra={"tenant_id": tenant_id})
            return KnowledgeResult(degraded=True, reason="circuit_open")

        start = self._clock()
        try:
            package = self._client.retrieve(
                query,
                tenant_id=tenant_id,
                security_context=security_context,
                correlation_id=correlation_id,
            )
        except KnowledgeError as exc:
            self._breaker.record_failure()
            logger.warning(
                "knowledge_retrieval_failed",
                extra={"tenant_id": tenant_id, "reason": exc.error_type},
            )
            return KnowledgeResult(degraded=True, reason=exc.error_type)

        self._breaker.record_success()
        latency_ms = round((self._clock() - start) * 1000.0, 3)
        logger.info(
            "knowledge_retrieved",
            extra={
                "tenant_id": tenant_id,
                "candidate_count": len(package.candidates),
                "latency_ms": latency_ms,
            },
        )
        return KnowledgeResult(
            package=package,
            degraded=False,
            candidate_count=len(package.candidates),
            latency_ms=latency_ms,
        )

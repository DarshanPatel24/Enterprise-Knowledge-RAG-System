"""Deployment readiness assessment (handbook Chapter 30, Chapter 5).

Produces an advisory readiness report over the deployment settings: worker-pool
sizing, replica count for high availability, resilience configuration, and the
NFR latency/accuracy thresholds. Advisory only --- it never changes behavior.
"""

from __future__ import annotations

from typing import Protocol

from domain.readiness.models import (
    ReadinessReport,
    error,
    info,
    warning,
)


class DeploymentSettingsLike(Protocol):
    """Structural view of the deployment settings the assessment reads."""

    vector_pool_size: int
    keyword_pool_size: int
    metadata_pool_size: int
    replicas: int
    circuit_breaker_threshold: int
    tenant_max_concurrent: int
    max_latency_ms: float
    min_availability: float


def assess_deployment_readiness(settings: DeploymentSettingsLike) -> ReadinessReport:
    """Assess deployment readiness from the deployment settings."""
    findings = []

    pools = {
        "vector": settings.vector_pool_size,
        "keyword": settings.keyword_pool_size,
        "metadata": settings.metadata_pool_size,
    }
    for name, size in pools.items():
        if size < 1:
            findings.append(error("worker_pool", f"{name} pool must have at least 1 worker"))
        else:
            findings.append(info("worker_pool", f"{name} pool size {size}"))

    if settings.replicas < 2:
        findings.append(
            warning("high_availability", "fewer than 2 replicas limits availability")
        )
    else:
        findings.append(info("high_availability", f"{settings.replicas} replicas configured"))

    if settings.circuit_breaker_threshold < 1:
        findings.append(error("resilience", "circuit breaker threshold must be positive"))
    else:
        findings.append(
            info("resilience", f"circuit breaker trips after {settings.circuit_breaker_threshold}")
        )

    if settings.tenant_max_concurrent == 0:
        findings.append(
            warning("multi_tenancy", "tenant concurrency is unlimited (no admission ceiling)")
        )
    else:
        findings.append(
            info("multi_tenancy", f"tenant concurrency ceiling {settings.tenant_max_concurrent}")
        )

    if settings.max_latency_ms > 500.0:
        findings.append(
            warning("latency_target", "latency budget exceeds the 500 ms NFR target")
        )
    else:
        findings.append(info("latency_target", f"latency budget {settings.max_latency_ms} ms"))

    if settings.min_availability < 0.999:
        findings.append(
            warning("availability_target", "availability target below 99.9% NFR")
        )
    else:
        findings.append(
            info("availability_target", f"availability target {settings.min_availability}")
        )

    return ReadinessReport(name="deployment", findings=tuple(findings))

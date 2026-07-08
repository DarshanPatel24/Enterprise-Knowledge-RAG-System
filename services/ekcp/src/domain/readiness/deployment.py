"""Deployment readiness assessment (handbook Chapter 18-19).

Assesses code-level deployment readiness across the control, runtime, and data
planes: high availability (replicas), resilience (circuit breaker), multi-tenant
admission, and the first-response-latency and availability NFR targets. Container
and cluster orchestration are out of scope (local-first); this validates the
configuration that governs a real deployment.
"""

from __future__ import annotations

from typing import Protocol

from domain.readiness.models import ReadinessReport, error, info, warning


class DeploymentSettingsLike(Protocol):
    """Structural view of the deployment settings the assessment reads."""

    replicas: int
    circuit_breaker_threshold: int
    tenant_max_concurrent: int
    first_response_latency_budget_ms: float
    min_availability: float


def assess_deployment_readiness(settings: DeploymentSettingsLike) -> ReadinessReport:
    """Assess deployment readiness from the deployment settings."""
    findings = [
        info(
            "planes",
            "control, runtime, and data planes are separated by configuration",
        )
    ]

    if settings.replicas < 2:
        findings.append(
            warning("high_availability", "fewer than 2 replicas limits availability")
        )
    else:
        findings.append(
            info("high_availability", f"{settings.replicas} replicas configured")
        )

    if settings.circuit_breaker_threshold < 1:
        findings.append(
            error("resilience", "circuit breaker threshold must be positive")
        )
    else:
        findings.append(
            info(
                "resilience",
                f"circuit breaker trips after {settings.circuit_breaker_threshold} failures",
            )
        )

    if settings.tenant_max_concurrent == 0:
        findings.append(
            warning(
                "multi_tenancy",
                "tenant concurrency is unlimited (no admission ceiling)",
            )
        )
    else:
        findings.append(
            info(
                "multi_tenancy",
                f"tenant concurrency ceiling {settings.tenant_max_concurrent}",
            )
        )

    if settings.first_response_latency_budget_ms > 3000.0:
        findings.append(
            warning(
                "latency_target",
                "first-response latency budget exceeds the 3 second NFR target",
            )
        )
    else:
        findings.append(
            info(
                "latency_target",
                f"first-response latency budget {settings.first_response_latency_budget_ms} ms",
            )
        )

    if settings.min_availability < 0.999:
        findings.append(
            warning("availability_target", "availability target below the 99.9% NFR")
        )
    else:
        findings.append(
            info(
                "availability_target",
                f"availability target {settings.min_availability}",
            )
        )

    return ReadinessReport(name="deployment", findings=tuple(findings))

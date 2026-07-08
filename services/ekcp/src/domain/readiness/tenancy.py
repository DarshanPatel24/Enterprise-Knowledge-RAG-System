"""Multi-tenant isolation and admission control (handbook Chapter 18).

Enforces a per-tenant concurrency ceiling (admission control) and assesses the
multi-tenant isolation posture: strict tenant boundaries via ``tenant_id`` and
tenant-aware structured observability. Isolation is logical by default (tenant
scoping on shared resources); physical isolation is a deployment choice.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol

from domain.readiness.models import ReadinessReport, info, warning


class TenantConcurrencyLimiter:
    """Enforce a per-tenant maximum of concurrent in-flight requests."""

    def __init__(self, max_concurrent: int) -> None:
        self._max_concurrent = max_concurrent
        self._active: dict[str, int] = {}

    def acquire(self, tenant_id: str) -> bool:
        """Try to admit a request for ``tenant_id``; return whether admitted."""
        if self._max_concurrent <= 0:
            return True
        current = self._active.get(tenant_id, 0)
        if current >= self._max_concurrent:
            return False
        self._active[tenant_id] = current + 1
        return True

    def release(self, tenant_id: str) -> None:
        """Release one in-flight slot for ``tenant_id``."""
        current = self._active.get(tenant_id, 0)
        if current > 0:
            self._active[tenant_id] = current - 1

    def active(self, tenant_id: str) -> int:
        """Return the number of in-flight requests for ``tenant_id``."""
        return self._active.get(tenant_id, 0)

    @contextmanager
    def slot(self, tenant_id: str) -> Iterator[bool]:
        """Context manager yielding whether the tenant was admitted."""
        admitted = self.acquire(tenant_id)
        try:
            yield admitted
        finally:
            if admitted:
                self.release(tenant_id)


class TenancySettingsLike(Protocol):
    """Structural view of the settings the tenancy assessment reads."""

    tenant_max_concurrent: int
    tenant_aware_observability: bool


def assess_multi_tenant_isolation(settings: TenancySettingsLike) -> ReadinessReport:
    """Assess the multi-tenant isolation posture from settings."""
    findings = [
        info(
            "tenant_boundary",
            "every request is scoped by X-Tenant-ID and filtered by tenant_id",
        )
    ]
    if settings.tenant_max_concurrent == 0:
        findings.append(
            warning(
                "tenant_admission",
                "tenant concurrency is unlimited (no per-tenant admission ceiling)",
            )
        )
    else:
        findings.append(
            info(
                "tenant_admission",
                f"per-tenant concurrency ceiling {settings.tenant_max_concurrent}",
            )
        )
    if settings.tenant_aware_observability:
        findings.append(
            info(
                "tenant_observability",
                "logs and traces carry tenant_id and correlation_id",
            )
        )
    else:
        findings.append(
            warning(
                "tenant_observability",
                "tenant-aware observability is disabled",
            )
        )
    return ReadinessReport(name="multi_tenancy", findings=tuple(findings))

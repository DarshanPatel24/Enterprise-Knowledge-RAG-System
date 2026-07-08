"""Deployment, multi-tenancy, and master handoff readiness domain tests."""

from __future__ import annotations

from typing import Any

from config.settings import DeploymentSettings
from domain.readiness import (
    HandoffKpis,
    Severity,
    TenantConcurrencyLimiter,
    assess_deployment_readiness,
    assess_handoff_readiness,
    assess_multi_tenant_isolation,
    build_master_handoff_package,
    default_handoff_kpis,
    error,
    info,
    warning,
)
from domain.readiness.models import ReadinessReport


def _deployment(**overrides: Any) -> DeploymentSettings:
    return DeploymentSettings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_report_ready_when_no_errors() -> None:
    report = ReadinessReport(
        name="x", findings=(info("a", "ok"), warning("b", "warn"))
    )
    assert report.ready is True
    assert len(report.warnings) == 1
    assert not report.errors


def test_report_not_ready_with_error() -> None:
    report = ReadinessReport(name="x", findings=(error("a", "bad"),))
    assert report.ready is False
    assert len(report.errors) == 1


def test_ready_is_serialized() -> None:
    report = ReadinessReport(name="x", findings=(info("a", "ok"),))
    assert report.model_dump()["ready"] is True


def test_deployment_ready_with_defaults() -> None:
    report = assess_deployment_readiness(_deployment())
    assert report.name == "deployment"
    assert report.ready is True


def test_deployment_low_replicas_warns() -> None:
    report = assess_deployment_readiness(_deployment(replicas=1))
    assert report.ready is True
    assert any(f.check == "high_availability" for f in report.warnings)


def test_deployment_unlimited_tenants_warns() -> None:
    report = assess_deployment_readiness(_deployment(tenant_max_concurrent=0))
    assert any(
        f.check == "multi_tenancy" and f.severity is Severity.WARNING
        for f in report.findings
    )


def test_multi_tenant_ready_with_defaults() -> None:
    report = assess_multi_tenant_isolation(_deployment())
    assert report.name == "multi_tenancy"
    assert report.ready is True


def test_multi_tenant_observability_disabled_warns() -> None:
    report = assess_multi_tenant_isolation(
        _deployment(tenant_aware_observability=False)
    )
    assert any(f.check == "tenant_observability" for f in report.warnings)


def test_tenant_limiter_admission() -> None:
    limiter = TenantConcurrencyLimiter(1)
    assert limiter.acquire("t") is True
    assert limiter.acquire("t") is False
    limiter.release("t")
    assert limiter.acquire("t") is True
    assert limiter.active("t") == 1


def test_tenant_limiter_zero_is_unlimited() -> None:
    limiter = TenantConcurrencyLimiter(0)
    assert limiter.acquire("t") is True
    assert limiter.acquire("t") is True


def test_tenant_limiter_slot_releases() -> None:
    limiter = TenantConcurrencyLimiter(1)
    with limiter.slot("t") as admitted:
        assert admitted is True
        assert limiter.active("t") == 1
    assert limiter.active("t") == 0


def test_handoff_ready_with_default_kpis() -> None:
    report = assess_handoff_readiness(default_handoff_kpis(), targets=_deployment())
    assert report.name == "master_handoff"
    assert report.ready is True


def test_handoff_below_target_fails() -> None:
    kpis = HandoffKpis(tool_success=0.5)
    report = assess_handoff_readiness(kpis, targets=_deployment())
    assert report.ready is False
    assert any(f.check == "tool_success" for f in report.errors)


def test_handoff_high_latency_warns_only() -> None:
    kpis = HandoffKpis(first_response_latency_ms=5000.0)
    report = assess_handoff_readiness(kpis, targets=_deployment())
    assert report.ready is True
    assert any(f.check == "first_response_latency" for f in report.warnings)


def test_master_handoff_package_assembly() -> None:
    kpis = default_handoff_kpis()
    report = assess_handoff_readiness(kpis, targets=_deployment())
    package = build_master_handoff_package(kpis, report)
    assert package.service == "ekcp"
    assert package.ready is True
    assert package.policy_enforcement_coverage == 1.0
    assert "POST /chat/stream" in package.endpoints
    assert "SecurityContext" in package.contracts
    assert package.report is not None

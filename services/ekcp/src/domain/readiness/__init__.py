"""Deployment, multi-tenancy, and master handoff readiness domain (handbook 18-23)."""

from domain.readiness.deployment import assess_deployment_readiness
from domain.readiness.handoff import (
    EKCP_CONTRACTS,
    EKCP_ENDPOINTS,
    HandoffKpis,
    MasterHandoffPackage,
    assess_handoff_readiness,
    build_master_handoff_package,
    default_handoff_kpis,
)
from domain.readiness.models import (
    ReadinessFinding,
    ReadinessReport,
    Severity,
    error,
    info,
    warning,
)
from domain.readiness.tenancy import (
    TenantConcurrencyLimiter,
    assess_multi_tenant_isolation,
)

__all__ = [
    "EKCP_CONTRACTS",
    "EKCP_ENDPOINTS",
    "HandoffKpis",
    "MasterHandoffPackage",
    "ReadinessFinding",
    "ReadinessReport",
    "Severity",
    "TenantConcurrencyLimiter",
    "assess_deployment_readiness",
    "assess_handoff_readiness",
    "assess_multi_tenant_isolation",
    "build_master_handoff_package",
    "default_handoff_kpis",
    "error",
    "info",
    "warning",
]

"""Deployment, multi-tenancy, and master handoff readiness endpoints.

Exposes the code-level readiness assessments (deployment topology, multi-tenant
isolation, and the master integration handoff KPIs) for operators, platform
health checks, and master integration sign-off. Container and cluster
orchestration are out of scope (local-first); these gates validate the readiness
a real deployment must satisfy.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import AppSettings
from composition import (
    build_deployment_readiness,
    build_master_handoff_package,
    build_multi_tenant_readiness,
)
from domain.readiness import MasterHandoffPackage, ReadinessReport

router = APIRouter(prefix="/v1/readiness", tags=["readiness"])


@router.get("", response_model=ReadinessReport)
async def deployment_readiness(settings: AppSettings) -> ReadinessReport:
    """Return the deployment readiness assessment."""
    return build_deployment_readiness(settings)


@router.get("/tenancy", response_model=ReadinessReport)
async def multi_tenant_readiness(settings: AppSettings) -> ReadinessReport:
    """Return the multi-tenant isolation readiness assessment."""
    return build_multi_tenant_readiness(settings)


@router.get("/handoff", response_model=MasterHandoffPackage)
async def master_handoff(settings: AppSettings) -> MasterHandoffPackage:
    """Return the master integration handoff package."""
    return build_master_handoff_package(settings)

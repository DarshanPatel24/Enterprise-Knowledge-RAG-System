"""Deployment readiness endpoint (handbook Chapters 30, 5).

Exposes the deployment readiness assessment (worker pools, high availability,
resilience, multi-tenancy, and NFR latency/accuracy targets) for operators and
platform health checks.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import AppSettings
from composition import build_deployment_readiness
from domain.readiness import ReadinessReport

router = APIRouter(prefix="/v1/readiness", tags=["readiness"])


@router.get("", response_model=ReadinessReport)
async def deployment_readiness(settings: AppSettings) -> ReadinessReport:
    """Return the deployment readiness assessment."""
    return build_deployment_readiness(settings)

"""Health endpoints for liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health probe response payload."""

    status: str
    service: str


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Return liveness status: the process is running and can serve requests."""
    return HealthResponse(status="ok", service="ekcp")


@router.get("/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    """Return readiness status for the EKCP service.

    S0 reports process readiness. Dependency checks (control plane, Redis, EKRE,
    model gateway) are wired in later sprints as those subsystems come online.
    """
    return HealthResponse(status="ready", service="ekcp")

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
def liveness() -> HealthResponse:
    """Return liveness status: the process is running and can serve requests."""
    return HealthResponse(status="ok", service="ekie")


@router.get("/ready", response_model=HealthResponse)
def readiness() -> HealthResponse:
    """Return readiness status for the EKIE service.

    S0 reports process readiness. Dependency checks (Control Plane, Qdrant,
    Redis, storage) are wired in later sprints as those subsystems come online.
    """
    return HealthResponse(status="ready", service="ekie")

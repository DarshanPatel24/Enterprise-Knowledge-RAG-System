"""Shared application resources and FastAPI dependencies for EKIE.

Builds the Control Plane database, asset storage, and the ingestion workflow
orchestrator once per process from environment-backed settings via the
composition root, then exposes them as FastAPI dependencies. Tests override
:func:`get_resources` to inject isolated, in-memory resources.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status

from composition import build_workflow_orchestrator
from config.settings import EkieSettings, get_settings
from domain.control_plane import ControlPlaneDatabase
from domain.observability import get_tenant_id
from domain.orchestration import WorkflowOrchestrator
from domain.storage import AssetStorage, InMemoryAssetStorage


@dataclass(frozen=True)
class AppResources:
    """Process-wide resources shared across API requests."""

    settings: EkieSettings
    db: ControlPlaneDatabase
    storage: AssetStorage
    orchestrator: WorkflowOrchestrator


_resources: AppResources | None = None


def build_resources(settings: EkieSettings) -> AppResources:
    """Construct application resources from settings via the composition root.

    Local environments provision the schema on startup; other environments rely
    on managed migrations. The storage backend is selected by
    :func:`composition.build_asset_storage` based on environment and endpoint
    configuration.
    """
    from composition import build_asset_storage

    db = ControlPlaneDatabase(settings.control_plane)
    if settings.environment == "local":
        db.create_all()
    storage: AssetStorage = build_asset_storage(settings)
    orchestrator = build_workflow_orchestrator(settings, db, storage)
    return AppResources(
        settings=settings, db=db, storage=storage, orchestrator=orchestrator
    )


def get_resources() -> AppResources:
    """Return the process-wide application resources, building them on first use."""
    global _resources
    if _resources is None:
        _resources = build_resources(get_settings())
    return _resources


def get_orchestrator(
    resources: Annotated[AppResources, Depends(get_resources)],
) -> WorkflowOrchestrator:
    """Return the ingestion workflow orchestrator."""
    return resources.orchestrator


def get_control_plane(
    resources: Annotated[AppResources, Depends(get_resources)],
) -> ControlPlaneDatabase:
    """Return the Control Plane database."""
    return resources.db


def require_tenant() -> str:
    """Return the tenant bound to the request, or raise 400 when absent."""
    tenant = get_tenant_id()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required",
        )
    return tenant

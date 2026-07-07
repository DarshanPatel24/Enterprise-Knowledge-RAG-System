"""Shared FastAPI dependencies for the EKCP API."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from config.settings import EkcpSettings, get_settings


def get_app_settings() -> EkcpSettings:
    """Return the process-wide EKCP settings."""
    return get_settings()


AppSettings = Annotated[EkcpSettings, Depends(get_app_settings)]


def require_tenant(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> str:
    """Return the tenant id from the request header, or reject with 400."""
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required",
        )
    return x_tenant_id


TenantId = Annotated[str, Depends(require_tenant)]

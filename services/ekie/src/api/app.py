"""FastAPI application factory for the EKIE service."""

from __future__ import annotations

from fastapi import FastAPI

from api.health import router as health_router
from api.middleware import CorrelationMiddleware
from config.settings import EkieSettings, get_settings
from domain.observability import configure_logging, get_logger


def create_app(settings: EkieSettings | None = None) -> FastAPI:
    """Build and configure the EKIE FastAPI application."""
    settings = settings or get_settings()
    configure_logging(
        service_name=settings.observability.service_name,
        log_level=settings.observability.log_level,
    )
    logger = get_logger("ekie.api")

    app = FastAPI(
        title="Enterprise Knowledge Ingestion Engine (EKIE)",
        version="0.1.0",
        description="Platform foundations and control plane (EKIE-S0).",
    )
    app.add_middleware(CorrelationMiddleware)
    app.include_router(health_router)

    logger.info("ekie_app_initialized", extra={"environment": settings.environment})
    return app


app = create_app()

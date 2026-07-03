"""FastAPI application factory for the EKIE service."""

from __future__ import annotations

from fastapi import FastAPI

from api.health import router as health_router
from api.ingestion import (
    repository_router as repository_ingestion_router,
)
from api.ingestion import router as ingestion_router
from api.middleware import CorrelationMiddleware
from composition import build_secret_provider
from config.settings import EkieSettings, get_settings
from domain.observability import configure_logging, get_logger
from domain.security import install_log_redaction


def create_app(settings: EkieSettings | None = None) -> FastAPI:
    """Build and configure the EKIE FastAPI application."""
    settings = settings or get_settings()
    configure_logging(
        service_name=settings.observability.service_name,
        log_level=settings.observability.log_level,
    )
    # Track configured secrets and scrub them from every log record (17.8).
    secret_provider = build_secret_provider(settings)
    install_log_redaction(secret_provider.registry)
    logger = get_logger("ekie.api")

    app = FastAPI(
        title="Enterprise Knowledge Ingestion Engine (EKIE)",
        version="0.1.0",
        description="Control plane and document ingestion workflow orchestration.",
    )
    app.add_middleware(CorrelationMiddleware)
    app.include_router(health_router)
    app.include_router(ingestion_router)
    app.include_router(repository_ingestion_router)

    logger.info("ekie_app_initialized", extra={"environment": settings.environment})
    return app


app = create_app()

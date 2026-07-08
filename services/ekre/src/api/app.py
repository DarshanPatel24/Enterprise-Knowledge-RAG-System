"""FastAPI application factory for the EKRE service."""

from __future__ import annotations

from fastapi import FastAPI

from api.candidates import router as candidates_router
from api.context import router as context_router
from api.execution import router as execution_router
from api.health import router as health_router
from api.middleware import CorrelationMiddleware, TenantQuotaMiddleware
from api.query import router as query_router
from api.ranking import router as ranking_router
from api.readiness import router as readiness_router
from api.retrieval import router as retrieval_router
from api.retrieve import router as retrieve_router
from composition import build_tenant_limiter, configure_observability
from config.settings import EkreSettings, get_settings
from domain.observability import get_logger


def create_app(settings: EkreSettings | None = None) -> FastAPI:
    """Build and configure the EKRE FastAPI application."""
    settings = settings or get_settings()
    configure_observability(settings)
    logger = get_logger("ekre.api")

    app = FastAPI(
        title="Enterprise Knowledge Retrieval Engine (EKRE)",
        version="0.1.0",
        description="Secure, deterministic, citation-preserving retrieval platform.",
    )
    app.add_middleware(TenantQuotaMiddleware, limiter=build_tenant_limiter(settings))
    app.add_middleware(CorrelationMiddleware)
    app.include_router(health_router)
    app.include_router(readiness_router)
    app.include_router(retrieval_router)
    app.include_router(query_router)
    app.include_router(execution_router)
    app.include_router(candidates_router)
    app.include_router(ranking_router)
    app.include_router(context_router)
    app.include_router(retrieve_router)

    logger.info("ekre_app_initialized", extra={"environment": settings.environment})
    return app


app = create_app()

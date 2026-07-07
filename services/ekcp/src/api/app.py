"""FastAPI application factory for the EKCP service."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router
from api.context import router as context_router
from api.conversation import router as conversation_router
from api.health import router as health_router
from api.middleware import CorrelationMiddleware
from api.prompt import router as prompt_router
from composition import configure_observability
from config.settings import EkcpSettings, get_settings
from domain.observability import get_logger


def _cors_origins(raw: str) -> list[str]:
    """Parse the comma-separated CORS origins setting into a list."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app(settings: EkcpSettings | None = None) -> FastAPI:
    """Build and configure the EKCP FastAPI application (single entry point)."""
    settings = settings or get_settings()
    configure_observability(settings)
    logger = get_logger("ekcp.api")

    app = FastAPI(
        title="Enterprise Knowledge Chat Platform (EKCP)",
        version="0.1.0",
        description="Governed conversational orchestration platform.",
    )

    origins = _cors_origins(settings.gateway.cors_allow_origins)
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(CorrelationMiddleware)

    app.include_router(health_router)
    app.include_router(conversation_router)
    app.include_router(context_router)
    app.include_router(prompt_router)
    app.include_router(chat_router)

    logger.info("ekcp_app_initialized", extra={"environment": settings.environment})
    return app


app = create_app()

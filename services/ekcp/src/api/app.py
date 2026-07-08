"""FastAPI application factory for the EKCP service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.agent import router as agent_router
from api.chat import router as chat_router
from api.context import router as context_router
from api.conversation import router as conversation_router
from api.governance import router as governance_router
from api.guards import enforce_tenant_limit, verify_gateway_auth
from api.health import router as health_router
from api.memory import router as memory_router
from api.middleware import CorrelationMiddleware
from api.model import router as model_router
from api.prompt import router as prompt_router
from api.readiness import router as readiness_router
from api.workflow import router as workflow_router
from composition import (
    build_tenant_limiter,
    configure_observability,
    configure_security,
)
from config.settings import EkcpSettings, get_settings
from domain.observability import get_logger


def _cors_origins(raw: str) -> list[str]:
    """Parse the comma-separated CORS origins setting into a list."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _warm_gateway(settings: EkcpSettings) -> None:
    """Build resources and load the chat model once at startup.

    Only runs for the real ``langchain`` runtime; the offline deterministic path
    needs no warmup. Any failure is logged and swallowed so a missing or slow
    model never prevents the API from starting.
    """
    if settings.model.runtime != "langchain":
        return
    logger = get_logger("ekcp.api")
    try:
        from api.dependencies import get_resources
        from domain.gateway import GenerationRequest

        resources = get_resources(settings)
        resources.model_gateway.invoke(
            GenerationRequest(prompt_text="warmup", tenant_id="warmup")
        )
        logger.info("ekcp_model_warmed")
    except Exception as exc:  # noqa: BLE001 - warmup must never crash startup
        logger.warning("ekcp_model_warmup_failed", extra={"error": str(exc)})


def create_app(settings: EkcpSettings | None = None) -> FastAPI:
    """Build and configure the EKCP FastAPI application (single entry point)."""
    settings = settings or get_settings()
    configure_observability(settings)
    configure_security(settings)
    logger = get_logger("ekcp.api")

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        _warm_gateway(settings)
        yield

    app = FastAPI(
        title="Enterprise Knowledge Chat Platform (EKCP)",
        version="0.1.0",
        description="Governed conversational orchestration platform.",
        lifespan=lifespan,
    )

    # Bind ingress-guard configuration to the app so guards honor the exact
    # settings this app was built with (never process-global state).
    app.state.security_settings = settings.security
    app.state.tenant_limiter = build_tenant_limiter(settings)

    origins = _cors_origins(settings.gateway.cors_allow_origins)
    if origins:
        # Never combine credentialed CORS with a wildcard origin.
        allow_credentials = "*" not in origins
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(CorrelationMiddleware)

    # Governed routes require the trusted gateway token (when enabled) and are
    # subject to per-tenant admission control. Health and readiness probes stay
    # open so orchestrators and load balancers can reach them.
    guarded = [Depends(verify_gateway_auth), Depends(enforce_tenant_limit)]

    app.include_router(health_router)
    app.include_router(conversation_router, dependencies=guarded)
    app.include_router(context_router, dependencies=guarded)
    app.include_router(prompt_router, dependencies=guarded)
    app.include_router(model_router, dependencies=guarded)
    app.include_router(memory_router, dependencies=guarded)
    app.include_router(agent_router, dependencies=guarded)
    app.include_router(governance_router, dependencies=guarded)
    app.include_router(workflow_router, dependencies=guarded)
    app.include_router(readiness_router)
    app.include_router(chat_router, dependencies=guarded)

    logger.info("ekcp_app_initialized", extra={"environment": settings.environment})
    return app


app = create_app()

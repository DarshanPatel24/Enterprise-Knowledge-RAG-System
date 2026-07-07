"""Shared FastAPI dependencies and application resources for the EKCP API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from composition import (
    build_context_assembler,
    build_context_store,
    build_conversation_engine,
    build_conversation_manager,
    build_conversation_store,
    build_event_sink,
    build_prompt_orchestrator,
    build_security_validator,
    build_session_manager,
    build_session_store,
)
from config.settings import EkcpSettings, get_settings
from domain.context import ContextAssembler, ContextStore
from domain.conversation import ConversationEngine, ConversationManager
from domain.prompt import PromptOrchestrator
from domain.security import SecurityContextValidator
from domain.session import SessionManager


def get_app_settings() -> EkcpSettings:
    """Return the process-wide EKCP settings."""
    return get_settings()


AppSettings = Annotated[EkcpSettings, Depends(get_app_settings)]


@dataclass(frozen=True)
class AppResources:
    """Composed, process-wide EKCP application resources.

    Conversation and session stores are in-memory singletons, so the resources
    must be shared across requests to preserve state within a process.
    """

    settings: EkcpSettings
    security_validator: SecurityContextValidator
    conversation_manager: ConversationManager
    session_manager: SessionManager
    engine: ConversationEngine
    context_assembler: ContextAssembler
    context_store: ContextStore
    prompt_orchestrator: PromptOrchestrator


def build_resources(settings: EkcpSettings) -> AppResources:
    """Build the application resources from settings via the composition root."""
    conversation_store = build_conversation_store(settings)
    session_store = build_session_store(settings)
    event_sink = build_event_sink(settings)
    return AppResources(
        settings=settings,
        security_validator=build_security_validator(settings),
        conversation_manager=build_conversation_manager(
            settings, conversation_store, event_sink=event_sink
        ),
        session_manager=build_session_manager(settings, session_store),
        engine=build_conversation_engine(
            settings, conversation_store, event_sink=event_sink
        ),
        context_assembler=build_context_assembler(settings),
        context_store=build_context_store(settings),
        prompt_orchestrator=build_prompt_orchestrator(settings),
    )


_resources: AppResources | None = None


def get_resources() -> AppResources:
    """Return the process-wide application resources, building them on first use."""
    global _resources
    if _resources is None:
        _resources = build_resources(get_settings())
    return _resources


Resources = Annotated[AppResources, Depends(get_resources)]


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

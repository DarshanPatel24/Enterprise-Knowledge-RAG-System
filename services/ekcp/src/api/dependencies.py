"""Shared FastAPI dependencies and application resources for the EKCP API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from composition import (
    build_agent_registry,
    build_agent_runtime,
    build_agent_selector,
    build_context_assembler,
    build_context_store,
    build_conversation_engine,
    build_conversation_manager,
    build_conversation_store,
    build_event_bus,
    build_event_sink,
    build_governance_guard,
    build_knowledge_retriever,
    build_memory_framework,
    build_model_gateway,
    build_planning_engine,
    build_prompt_orchestrator,
    build_security_validator,
    build_session_manager,
    build_session_store,
    build_tool_executor,
    build_workflow_orchestrator,
)
from config.settings import EkcpSettings, get_settings
from domain.agents import (
    AgentPolicy,
    AgentRegistry,
    AgentRuntime,
    AgentSelector,
)
from domain.context import ContextAssembler, ContextStore
from domain.conversation import ConversationEngine, ConversationManager
from domain.gateway import LLMGateway
from domain.governance import (
    GovernanceError,
    GovernanceGuard,
    GovernancePolicy,
    Principal,
    Role,
    parse_clearance,
)
from domain.knowledge import KnowledgeRetriever
from domain.memory import MemoryFramework
from domain.planning import PlanningEngine
from domain.prompt import PromptOrchestrator
from domain.security import SecurityContextValidator
from domain.session import SessionManager
from domain.tools import ToolExecutor
from domain.workflow import EventBus, WorkflowOrchestrator


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
    model_gateway: LLMGateway
    memory_framework: MemoryFramework
    tool_executor: ToolExecutor
    agent_registry: AgentRegistry
    agent_selector: AgentSelector
    agent_runtime: AgentRuntime
    agent_policy: AgentPolicy
    planning_engine: PlanningEngine
    governance_guard: GovernanceGuard
    governance_policy: GovernancePolicy
    knowledge_retriever: KnowledgeRetriever
    workflow_orchestrator: WorkflowOrchestrator
    event_bus: EventBus


def build_resources(settings: EkcpSettings) -> AppResources:
    """Build the application resources from settings via the composition root."""
    conversation_store = build_conversation_store(settings)
    session_store = build_session_store(settings)
    event_sink = build_event_sink(settings)
    event_bus = build_event_bus(settings)
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
        model_gateway=build_model_gateway(settings),
        memory_framework=build_memory_framework(settings),
        tool_executor=build_tool_executor(settings),
        agent_registry=build_agent_registry(settings),
        agent_selector=build_agent_selector(settings),
        agent_runtime=build_agent_runtime(settings),
        agent_policy=AgentPolicy.from_settings(settings.agent),  # type: ignore[arg-type]
        planning_engine=build_planning_engine(settings),
        governance_guard=build_governance_guard(settings),
        governance_policy=GovernancePolicy.from_settings(settings.governance),  # type: ignore[arg-type]
        knowledge_retriever=build_knowledge_retriever(settings),
        workflow_orchestrator=build_workflow_orchestrator(settings, event_bus=event_bus),
        event_bus=event_bus,
    )


_resources_cache: dict[int, AppResources] = {}


def get_resources(
    settings: Annotated[EkcpSettings, Depends(get_app_settings)],
) -> AppResources:
    """Return application resources for ``settings``, building once per settings.

    Depending on the overridable ``get_app_settings`` lets tests inject hermetic
    settings (so the API exercises the deterministic offline path), while
    production reuses the single cached settings object and builds resources once.
    """
    key = id(settings)
    cached = _resources_cache.get(key)
    if cached is None:
        cached = build_resources(settings)
        _resources_cache[key] = cached
    return cached


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


def build_principal(
    resources: AppResources,
    *,
    user_id: str,
    tenant_id: str,
    clearance: str,
    roles: list[str] | None = None,
) -> Principal:
    """Build a governance principal from request identity and role assignment.

    Roles default to the configured default role. When
    ``security.trust_request_roles`` is false, client-supplied roles are ignored
    entirely and only the configured default role applies, so a caller can never
    self-elevate by asserting roles in the request body. An unknown role or
    clearance is rejected with a 422 so governance never runs on an invalid
    principal.
    """
    if not resources.settings.security.trust_request_roles:
        roles = None
    try:
        resolved_roles = (
            frozenset(Role(role) for role in roles)
            if roles
            else frozenset({resources.governance_policy.default_role})
        )
        resolved_clearance = parse_clearance(clearance)
    except (ValueError, GovernanceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return Principal(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=resolved_roles,
        clearance=resolved_clearance,
    )

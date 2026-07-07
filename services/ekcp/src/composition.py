"""Composition root: build EKCP foundations from settings.

Wires the settings module into engine-owned domain objects (config over code).
Domain packages stay independent of the settings module; this root is the single
place that reads settings and injects dependencies. The root grows one builder
at a time as the sprint track advances.
"""

from __future__ import annotations

from config.settings import EkcpSettings
from domain.agents import (
    AgentCoordinator,
    AgentPolicy,
    AgentRegistry,
    AgentRuntime,
    AgentSelector,
    default_agent_registry,
    runner_from_policy,
)
from domain.context import (
    ContextAssembler,
    ContextPolicy,
    ContextStore,
    InMemoryContextStore,
)
from domain.conversation import (
    ConversationEngine,
    ConversationManager,
    ConversationPolicy,
    EventSink,
    InMemoryConversationStore,
    InMemoryEventSink,
    LoggingEventSink,
)
from domain.gateway import (
    CostProfile,
    GatewayPolicy,
    LLMGateway,
    Modality,
    ModelDescriptor,
    ModelLifecycleState,
    ModelRegistry,
    ModelSelector,
    default_model_registry,
    provider_registry_from_settings,
)
from domain.governance import (
    GovernanceGuard,
    GovernancePolicy,
    InMemoryAuditSink,
    LoggingAuditSink,
    Masker,
    MaskingConfig,
    PolicyEngine,
    SecretRegistry,
    SecurityContextPropagator,
    install_log_redaction,
)
from domain.intent import IntentClassifier, IntentGate, IntentPolicy
from domain.memory import (
    InMemoryMemoryStore,
    MemoryFramework,
    MemoryPolicy,
    MemoryStore,
)
from domain.observability import build_langfuse_callbacks, configure_logging
from domain.planning import PlanningEngine, PlanningPolicy
from domain.prompt import (
    PromptOrchestrator,
    PromptPolicy,
    default_prompt_registry,
)
from domain.security import SecurityContextValidator
from domain.session import InMemorySessionStore, SessionManager
from domain.tools import (
    ToolExecutor,
    ToolPolicy,
    ToolRegistry,
    default_tool_registry,
)

_LANGCHAIN_MODEL_ID = "ekcp-chat"

__all__ = [
    "build_agent_coordinator",
    "build_agent_registry",
    "build_agent_runtime",
    "build_agent_selector",
    "build_context_assembler",
    "build_context_store",
    "build_conversation_engine",
    "build_conversation_manager",
    "build_conversation_store",
    "build_event_sink",
    "build_governance_guard",
    "build_intent_gate",
    "build_memory_framework",
    "build_memory_store",
    "build_model_gateway",
    "build_planning_engine",
    "build_prompt_orchestrator",
    "build_secret_registry",
    "build_security_validator",
    "build_session_manager",
    "build_session_store",
    "build_tool_executor",
    "build_tool_registry",
    "build_tracing_callbacks",
    "configure_observability",
    "configure_security",
]


def configure_observability(settings: EkcpSettings) -> None:
    """Install structured JSON logging from the observability settings."""
    configure_logging(
        service_name=settings.observability.service_name,
        log_level=settings.observability.log_level,
    )


def build_security_validator(settings: EkcpSettings) -> SecurityContextValidator:
    """Build the security context ingress validator from settings."""
    return SecurityContextValidator.from_settings(settings.security)


def build_tracing_callbacks(settings: EkcpSettings) -> list[object]:
    """Build Langfuse tracing callbacks from settings (empty when disabled)."""
    return list(build_langfuse_callbacks(settings.observability))


def build_conversation_store(settings: EkcpSettings) -> InMemoryConversationStore:
    """Build the conversation store (in-memory offline default)."""
    _ = settings.control_plane  # driver=mssql wires the SQL Server store in a later sprint
    return InMemoryConversationStore()


def build_event_sink(settings: EkcpSettings) -> EventSink:
    """Build the conversation event sink from settings."""
    if settings.conversation.event_sink == "logging":
        return LoggingEventSink()
    return InMemoryEventSink()


def build_conversation_manager(
    settings: EkcpSettings,
    store: InMemoryConversationStore,
    *,
    event_sink: EventSink | None = None,
) -> ConversationManager:
    """Build the conversation administration manager from settings."""
    policy = ConversationPolicy.from_settings(settings.conversation)
    return ConversationManager(store, policy=policy, event_sink=event_sink)


def build_session_store(settings: EkcpSettings) -> InMemorySessionStore:
    """Build the session store (in-memory offline default)."""
    _ = settings.redis  # enabled=True wires the Redis session store in a later sprint
    return InMemorySessionStore()


def build_session_manager(
    settings: EkcpSettings, store: InMemorySessionStore
) -> SessionManager:
    """Build the session manager from settings."""
    return SessionManager(
        store, session_ttl_seconds=settings.session.session_ttl_seconds
    )


def build_intent_gate(settings: EkcpSettings) -> IntentGate:
    """Build the intent-before-execution gate from settings."""
    policy = IntentPolicy.from_settings(settings.intent)
    return IntentGate(IntentClassifier(policy))


def build_conversation_engine(
    settings: EkcpSettings,
    store: InMemoryConversationStore,
    *,
    intent_gate: IntentGate | None = None,
    event_sink: EventSink | None = None,
) -> ConversationEngine:
    """Build the conversation engine (core interaction loop) from settings."""
    return ConversationEngine(
        store=store,
        intent_gate=intent_gate or build_intent_gate(settings),
        event_sink=event_sink,
        enable_events=settings.conversation.enable_events,
    )


def build_context_store(settings: EkcpSettings) -> ContextStore:
    """Build the context package store (in-memory offline default)."""
    _ = settings.redis  # enabled=True wires a cache-backed store in a later sprint
    return InMemoryContextStore()


def build_context_assembler(settings: EkcpSettings) -> ContextAssembler:
    """Build the context assembler from settings."""
    return ContextAssembler(ContextPolicy.from_settings(settings.context))


def build_prompt_orchestrator(settings: EkcpSettings) -> PromptOrchestrator:
    """Build the prompt orchestrator from settings and the template registry."""
    return PromptOrchestrator(
        PromptPolicy.from_settings(settings.prompt),
        registry=default_prompt_registry(),
    )


def build_memory_store(settings: EkcpSettings) -> MemoryStore:
    """Build the memory store (in-memory offline default)."""
    _ = settings.control_plane  # driver=mssql wires a durable memory store later
    return InMemoryMemoryStore()


def build_memory_framework(
    settings: EkcpSettings, store: MemoryStore | None = None
) -> MemoryFramework:
    """Build the memory framework facade from settings."""
    return MemoryFramework(
        store or build_memory_store(settings),
        MemoryPolicy.from_settings(settings.memory),
    )


def build_tool_registry(settings: EkcpSettings) -> ToolRegistry:
    """Build the tool registry seeded with the deterministic sample tools."""
    _ = settings
    return default_tool_registry()


def build_tool_executor(
    settings: EkcpSettings, registry: ToolRegistry | None = None
) -> ToolExecutor:
    """Build the governed tool executor from settings."""
    return ToolExecutor(
        registry or build_tool_registry(settings),
        ToolPolicy.from_settings(settings.tools),
    )


def build_agent_registry(settings: EkcpSettings) -> AgentRegistry:
    """Build the agent registry seeded with the deterministic sample agents."""
    _ = settings
    return default_agent_registry()


def build_agent_selector(settings: EkcpSettings) -> AgentSelector:
    """Build the capability-based agent selector."""
    _ = settings
    return AgentSelector()


def build_agent_runtime(settings: EkcpSettings) -> AgentRuntime:
    """Build the agent runtime from settings (sequential default)."""
    return runner_from_policy(AgentPolicy.from_settings(settings.agent))  # type: ignore[arg-type]


def build_agent_coordinator(settings: EkcpSettings) -> AgentCoordinator:
    """Build the multi-agent coordinator from settings."""
    return AgentCoordinator(
        build_agent_registry(settings),
        build_agent_selector(settings),
        build_agent_runtime(settings),
    )


def build_planning_engine(settings: EkcpSettings) -> PlanningEngine:
    """Build the planning engine from settings."""
    return PlanningEngine(PlanningPolicy.from_settings(settings.planning))


def build_governance_guard(settings: EkcpSettings) -> GovernanceGuard:
    """Build the governance guard (policy enforcement point) from settings."""
    policy = GovernancePolicy.from_settings(settings.governance)  # type: ignore[arg-type]
    engine = PolicyEngine(
        enforce_authorization=policy.enforce_authorization,
        policy_version=policy.policy_version,
    )
    sink = LoggingAuditSink() if policy.audit_sink == "logging" else InMemoryAuditSink()
    masker = Masker(
        MaskingConfig(
            enabled=policy.enable_masking,
            email=policy.mask_email,
            phone=policy.mask_phone,
            ssn=policy.mask_ssn,
            credit_card=policy.mask_credit_card,
        )
    )
    propagator = SecurityContextPropagator(
        allow_downgrade=policy.allow_classification_downgrade
    )
    return GovernanceGuard(engine, sink, masker, propagator, policy=policy)


def build_secret_registry(settings: EkcpSettings) -> SecretRegistry:
    """Build a secret registry primed with the non-empty secrets from settings."""
    registry = SecretRegistry()
    for secret in (
        settings.observability.langfuse_public_key,
        settings.observability.langfuse_secret_key,
        settings.redis.password,
        settings.control_plane.url,
    ):
        registry.register(secret)
    return registry


def configure_security(settings: EkcpSettings) -> SecretRegistry:
    """Prime the secret registry and install log redaction (call after logging)."""
    registry = build_secret_registry(settings)
    install_log_redaction(registry)
    return registry


def _build_model_registry(settings: EkcpSettings) -> ModelRegistry:
    """Build the model registry, adding the configured chat model when selected."""
    registry = default_model_registry()
    model = settings.model
    if model.runtime == "langchain":
        registry.register(
            ModelDescriptor(
                model_id=_LANGCHAIN_MODEL_ID,
                provider=model.provider,
                model_name=model.model_name,
                runtime="langchain",
                modalities=frozenset({Modality.TEXT, Modality.STREAMING}),
                context_window=model.context_window,
                max_output_tokens=model.max_output_tokens,
                cost_profile=CostProfile(
                    prompt_cost_per_1k=model.prompt_cost_per_1k,
                    completion_cost_per_1k=model.completion_cost_per_1k,
                ),
                quality_score=0.8,
                lifecycle_state=ModelLifecycleState.PRODUCTION,
                base_url=model.base_url,
                temperature=model.temperature,
            )
        )
    return registry


def build_model_gateway(settings: EkcpSettings) -> LLMGateway:
    """Build the model-agnostic LLM gateway from settings."""
    model = settings.model
    policy = GatewayPolicy.from_settings(model)  # type: ignore[arg-type]
    if model.runtime == "langchain" and not model.default_model_id:
        policy = policy.model_copy(update={"default_model_id": _LANGCHAIN_MODEL_ID})
    registry = _build_model_registry(settings)
    selector = ModelSelector(
        strategy=policy.routing_strategy, require_approved=policy.require_approved
    )
    providers = provider_registry_from_settings(model.runtime)
    return LLMGateway(
        registry=registry,
        selector=selector,
        providers=providers,
        policy=policy,
    )

"""Environment-backed configuration for the EKCP service.

All operational values are configuration-driven (configuration over code). No
credentials, endpoints, models, or limits are hardcoded; values load from the
process environment or a local ``.env`` file with the ``EKCP_`` prefix.

The settings object grows one subsystem at a time as the sprint track advances.
S0 establishes the gateway, observability, security, cache, and control-plane
baselines. Domain packages never import this module directly; the composition
root reads settings and injects dependencies.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the .env file co-located with services/ekcp/ regardless of
# the process working directory, preventing silent settings fall-through when
# uvicorn or scripts start from the repository root.
# Path hierarchy from this file (services/ekcp/src/config/settings.py):
#   parents[0] = config/
#   parents[1] = src/
#   parents[2] = services/ekcp/   <-- .env lives here
_ENV_FILE = str(Path(__file__).resolve().parents[2] / ".env")


class GatewaySettings(BaseSettings):
    """API gateway (single entry point) network and routing settings."""

    model_config = SettingsConfigDict(env_prefix="EKCP_GATEWAY__", extra="ignore")

    host: str = "0.0.0.0"  # noqa: S104 - service binds all interfaces in container/dev
    port: int = Field(default=8003, gt=0)
    cors_allow_origins: str = ""
    request_timeout_seconds: float = Field(default=30.0, gt=0.0)


class ObservabilitySettings(BaseSettings):
    """Observability settings for logging, tracing, and Langfuse."""

    model_config = SettingsConfigDict(env_prefix="EKCP_OBSERVABILITY__", extra="ignore")

    log_level: str = "INFO"
    service_name: str = "ekcp"
    langfuse_enabled: bool = False
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    otel_exporter_endpoint: str | None = None


class SecuritySettings(BaseSettings):
    """Security context ingress settings enforced before conversation execution.

    When ``require_security_context`` is true every governed request must carry a
    valid security context; execution never proceeds without one. When
    ``require_gateway_auth`` is true, every governed request must additionally
    present the shared ``gateway_auth_token`` (bearer token), enforcing that only
    the trusted upstream gateway can reach EKCP.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_SECURITY__", extra="ignore")

    require_security_context: bool = True
    default_clearance: Literal["public", "internal", "confidential", "restricted"] = "public"
    require_gateway_auth: bool = False
    gateway_auth_token: str = ""
    trust_request_roles: bool = True


class RedisSettings(BaseSettings):
    """Redis cache/session backend settings (config-selected behind seams).

    The offline default keeps EKCP fully in-memory; ``enabled`` switches session
    and cache state to a live Redis instance without any code change.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_REDIS__", extra="ignore")

    enabled: bool = False
    host: str = "localhost"
    port: int = Field(default=6379, gt=0)
    db: int = Field(default=0, ge=0)
    password: str = ""
    request_timeout_seconds: float = Field(default=5.0, gt=0.0)


class ControlPlaneSettings(BaseSettings):
    """Conversation control-plane persistence settings.

    The offline default is an in-memory store; ``driver=mssql`` selects the
    Microsoft SQL Server control plane via the connection ``url`` without any
    change to conversation logic.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_CONTROL_PLANE__", extra="ignore")

    driver: Literal["inmemory", "mssql"] = "inmemory"
    url: str = ""


class ConversationSettings(BaseSettings):
    """Conversation lifecycle and Conversation Digital Twin settings."""

    model_config = SettingsConfigDict(env_prefix="EKCP_CONVERSATION__", extra="ignore")

    default_workspace_id: str = "default"
    default_language: str = "en"
    default_priority: str = "normal"
    archive_on_complete: bool = False
    enable_events: bool = True
    event_sink: Literal["memory", "logging"] = "memory"


class SessionSettings(BaseSettings):
    """Session and state management settings."""

    model_config = SettingsConfigDict(env_prefix="EKCP_SESSION__", extra="ignore")

    session_ttl_seconds: float = Field(default=3600.0, gt=0.0)
    max_concurrent_sessions: int = Field(default=8, ge=0)


class IntentSettings(BaseSettings):
    """Intent gating and confidence policy settings.

    The pipeline is deterministic by default. The confidence threshold governs
    when the gate requests clarification instead of executing on ambiguous input.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_INTENT__", extra="ignore")

    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    default_language: str = "en"
    enable_llm_intent: bool = False


class ContextSettings(BaseSettings):
    """Context orchestration (assembly and budgeting) settings."""

    model_config = SettingsConfigDict(env_prefix="EKCP_CONTEXT__", extra="ignore")

    max_context_tokens: int = Field(default=8000, gt=0)
    chars_per_token: int = Field(default=4, gt=0)
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    dedupe_content: bool = True
    reserve_ratio: float = Field(default=0.1, ge=0.0, lt=1.0)


class PromptSettings(BaseSettings):
    """Prompt orchestration (construction and budgeting) settings.

    Prompts are constructed from declarative templates with explicit variables;
    the assistant identity and behavior are configuration-driven, not hardcoded.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_PROMPT__", extra="ignore")

    default_template_id: str = "enterprise_chat_v1"
    max_prompt_tokens: int = Field(default=12000, gt=0)
    chars_per_token: int = Field(default=4, gt=0)
    assistant_identity: str = "the enterprise knowledge assistant"
    assistant_behavior: str = "Be accurate, concise, and policy-compliant."
    default_output_format: str = "markdown"


class ModelGatewaySettings(BaseSettings):
    """Model management and LLM gateway settings.

    The offline default runtime is ``deterministic`` (a dependency-free echo
    model) so the gateway runs with no external provider. Selecting
    ``runtime=langchain`` routes to the configured HuggingFace or Ollama chat
    model behind the gateway seam; no provider is hardcoded and token accounting
    is always enforced.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_MODEL__", extra="ignore")

    runtime: Literal["deterministic", "langchain"] = "deterministic"
    provider: Literal["huggingface", "ollama"] = "huggingface"
    model_name: str = ""
    base_url: str = "http://localhost:11434"
    temperature: float = Field(default=0.0, ge=0.0)
    context_window: int = Field(default=8192, gt=0)
    max_output_tokens: int = Field(default=2048, gt=0)
    prompt_cost_per_1k: float = Field(default=0.0, ge=0.0)
    completion_cost_per_1k: float = Field(default=0.0, ge=0.0)
    routing_strategy: Literal[
        "capability", "cost", "latency", "quality", "policy", "hybrid"
    ] = "hybrid"
    default_model_id: str = ""
    enable_fallback: bool = True
    require_approved: bool = True
    max_tokens_per_request: int = Field(default=0, ge=0)
    max_cost_per_request: float = Field(default=0.0, ge=0.0)
    chars_per_token: int = Field(default=4, gt=0)


class MemorySettings(BaseSettings):
    """Memory framework (tiers, retrieval, retention) settings.

    Per-scope TTLs govern retention; a TTL of 0 means indefinite retention
    (organizational memory). Retrieval ranking weights and the confidence
    threshold are configuration-driven, not hardcoded.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_MEMORY__", extra="ignore")

    working_ttl_seconds: float = Field(default=1800.0, ge=0.0)
    session_ttl_seconds: float = Field(default=28800.0, ge=0.0)
    conversation_ttl_seconds: float = Field(default=2592000.0, ge=0.0)
    workspace_ttl_seconds: float = Field(default=31536000.0, ge=0.0)
    user_ttl_seconds: float = Field(default=94608000.0, ge=0.0)
    organizational_ttl_seconds: float = Field(default=0.0, ge=0.0)
    default_min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    default_classification: str = "internal"
    max_retrieval_limit: int = Field(default=10, gt=0)
    weight_relevance: float = Field(default=0.4, ge=0.0)
    weight_recency: float = Field(default=0.2, ge=0.0)
    weight_importance: float = Field(default=0.15, ge=0.0)
    weight_frequency: float = Field(default=0.1, ge=0.0)
    weight_trust: float = Field(default=0.15, ge=0.0)
    recency_half_life_hours: float = Field(default=24.0, gt=0.0)


class ToolSettings(BaseSettings):
    """Tool execution platform settings."""

    model_config = SettingsConfigDict(env_prefix="EKCP_TOOLS__", extra="ignore")

    default_timeout_seconds: float = Field(default=10.0, gt=0.0)
    max_attempts: int = Field(default=2, ge=1)
    enforce_permissions: bool = True


class AgentSettings(BaseSettings):
    """Agent runtime settings.

    The offline default runner is ``sequential`` (deterministic, in-process).
    Selecting ``langgraph`` routes agent execution through a LangGraph graph with
    a checkpointer for recovery; steps are bounded to prevent runaway loops.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_AGENT__", extra="ignore")

    runner: Literal["sequential", "langgraph"] = "sequential"
    max_steps: int = Field(default=4, gt=0)
    base_confidence: float = Field(default=0.85, ge=0.0, le=1.0)


class PlanningSettings(BaseSettings):
    """Planning and orchestration settings."""

    model_config = SettingsConfigDict(env_prefix="EKCP_PLANNING__", extra="ignore")

    max_tasks: int = Field(default=12, gt=0)
    default_task_timeout_seconds: float = Field(default=60.0, gt=0.0)


class GovernanceSettings(BaseSettings):
    """Governance, security, and policy settings.

    Policy enforcement and auditing are on by default so every governed
    operation is authorized and recorded. Masking and secret redaction protect
    outbound responses and logs. Classification downgrades are blocked by default.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_GOVERNANCE__", extra="ignore")

    enforce_authorization: bool = True
    enable_audit: bool = True
    audit_sink: Literal["memory", "logging", "file"] = "memory"
    audit_file_path: str = "./storage/audit/ekcp_audit.jsonl"
    enable_masking: bool = True
    mask_email: bool = True
    mask_phone: bool = True
    mask_ssn: bool = True
    mask_credit_card: bool = True
    mask_inbound: bool = True
    allow_classification_downgrade: bool = False
    policy_version: str = "v1"
    default_role: Literal["admin", "power_user", "user", "service", "agent"] = (
        "power_user"
    )


class KnowledgeSettings(BaseSettings):
    """Enterprise knowledge integration (EKRE consumption) settings.

    Knowledge is disabled by default so the offline path never requires a live
    EKRE; enabling it routes retrieval through the EKRE HTTP client behind a
    circuit breaker, degrading gracefully to local memory when EKRE is
    unavailable. The EKRE base URL is configuration-driven.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_KNOWLEDGE__", extra="ignore")

    enabled: bool = False
    base_url: str = "http://localhost:8002"
    timeout_seconds: float = Field(default=10.0, gt=0.0)
    max_retries: int = Field(default=3, ge=0)
    circuit_breaker_threshold: int = Field(default=5, gt=0)
    circuit_breaker_reset_seconds: float = Field(default=60.0, gt=0.0)
    retrieval_mode: Literal["semantic", "keyword", "hybrid"] = "hybrid"
    max_candidates: int = Field(default=10, gt=0)
    relevance_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class WorkflowSettings(BaseSettings):
    """Workflow and event orchestration settings."""

    model_config = SettingsConfigDict(env_prefix="EKCP_WORKFLOW__", extra="ignore")

    enable_events: bool = True
    event_bus: Literal["memory", "logging"] = "memory"
    source_service: str = "ekcp"


class DeploymentSettings(BaseSettings):
    """Deployment, multi-tenancy, and master handoff readiness settings.

    Deployment topology is separate from business logic; these values tune high
    availability (replicas), resilience, multi-tenant admission, and the NFR and
    KPI targets validated for master integration handoff. Container and cluster
    orchestration are out of scope (local-first); this configures the readiness
    gates a real deployment must satisfy.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_DEPLOYMENT__", extra="ignore")

    replicas: int = Field(default=2, gt=0)
    circuit_breaker_threshold: int = Field(default=5, gt=0)
    tenant_max_concurrent: int = Field(default=8, ge=0)
    tenant_aware_observability: bool = True
    first_response_latency_budget_ms: float = Field(default=3000.0, gt=0.0)
    min_availability: float = Field(default=0.999, ge=0.0, le=1.0)
    min_conversation_completion: float = Field(default=0.99, ge=0.0, le=1.0)
    min_tool_success: float = Field(default=0.99, ge=0.0, le=1.0)
    min_agent_orchestration: float = Field(default=0.99, ge=0.0, le=1.0)
    min_conversation_recovery: float = Field(default=1.0, ge=0.0, le=1.0)
    min_policy_coverage: float = Field(default=1.0, ge=0.0, le=1.0)
    min_audit_coverage: float = Field(default=1.0, ge=0.0, le=1.0)


class EkcpSettings(BaseSettings):
    """Top-level EKCP settings composed of engine subsystem settings."""

    model_config = SettingsConfigDict(
        env_prefix="EKCP_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "ekcp"
    environment: str = "local"

    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    control_plane: ControlPlaneSettings = Field(default_factory=ControlPlaneSettings)
    conversation: ConversationSettings = Field(default_factory=ConversationSettings)
    session: SessionSettings = Field(default_factory=SessionSettings)
    intent: IntentSettings = Field(default_factory=IntentSettings)
    context: ContextSettings = Field(default_factory=ContextSettings)
    prompt: PromptSettings = Field(default_factory=PromptSettings)
    model: ModelGatewaySettings = Field(default_factory=ModelGatewaySettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    tools: ToolSettings = Field(default_factory=ToolSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    planning: PlanningSettings = Field(default_factory=PlanningSettings)
    governance: GovernanceSettings = Field(default_factory=GovernanceSettings)
    knowledge: KnowledgeSettings = Field(default_factory=KnowledgeSettings)
    workflow: WorkflowSettings = Field(default_factory=WorkflowSettings)
    deployment: DeploymentSettings = Field(default_factory=DeploymentSettings)


@lru_cache(maxsize=1)
def get_settings() -> EkcpSettings:
    """Return a cached, process-wide EKCP settings instance."""
    return EkcpSettings()

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
    valid security context; execution never proceeds without one.
    """

    model_config = SettingsConfigDict(env_prefix="EKCP_SECURITY__", extra="ignore")

    require_security_context: bool = True
    default_clearance: Literal["public", "internal", "confidential", "restricted"] = "public"


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


@lru_cache(maxsize=1)
def get_settings() -> EkcpSettings:
    """Return a cached, process-wide EKCP settings instance."""
    return EkcpSettings()

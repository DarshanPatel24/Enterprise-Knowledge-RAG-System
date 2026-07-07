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


@lru_cache(maxsize=1)
def get_settings() -> EkcpSettings:
    """Return a cached, process-wide EKCP settings instance."""
    return EkcpSettings()

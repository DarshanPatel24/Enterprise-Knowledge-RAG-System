"""Model gateway policy resolved from settings."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from domain.gateway.models import RoutingStrategy


class ModelSettingsLike(Protocol):
    """Structural view of the model settings the policy depends on."""

    runtime: str
    provider: str
    model_name: str
    base_url: str
    temperature: float
    context_window: int
    max_output_tokens: int
    prompt_cost_per_1k: float
    completion_cost_per_1k: float
    routing_strategy: str
    default_model_id: str
    enable_fallback: bool
    require_approved: bool
    max_tokens_per_request: int
    max_cost_per_request: float
    chars_per_token: int


class GatewayPolicy(BaseModel):
    """Immutable model gateway policy resolved from settings."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    routing_strategy: RoutingStrategy = RoutingStrategy.HYBRID
    default_model_id: str = "ekcp-echo"
    enable_fallback: bool = True
    require_approved: bool = True
    max_tokens_per_request: int = Field(default=0, ge=0)
    max_cost_per_request: float = Field(default=0.0, ge=0.0)
    chars_per_token: int = Field(default=4, gt=0)

    @classmethod
    def from_settings(cls, settings: ModelSettingsLike) -> GatewayPolicy:
        """Build the gateway policy from the model settings."""
        return cls(
            routing_strategy=RoutingStrategy(settings.routing_strategy),
            default_model_id=settings.default_model_id or "ekcp-echo",
            enable_fallback=settings.enable_fallback,
            require_approved=settings.require_approved,
            max_tokens_per_request=settings.max_tokens_per_request,
            max_cost_per_request=settings.max_cost_per_request,
            chars_per_token=settings.chars_per_token,
        )

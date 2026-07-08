"""Model gateway models: registry entries and the Model Invocation Contract.

Implements the handbook Model Invocation Contract (Chapter 14): a normalized
request and a normalized response so no platform component ever depends on a
provider-specific shape. All models are frozen. Token accounting is mandatory:
every response carries a :class:`TokenUsage` and a cost estimate.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Modality(StrEnum):
    """Model capability advertised by a registered model (handbook 14.7)."""

    TEXT = "text"
    VISION = "vision"
    AUDIO = "audio"
    FUNCTION_CALLING = "function_calling"
    JSON_OUTPUT = "json_output"
    STREAMING = "streaming"
    LONG_CONTEXT = "long_context"
    MULTILINGUAL = "multilingual"


class ModelLifecycleState(StrEnum):
    """Model lifecycle states (handbook 14.16). Only approved states serve."""

    REGISTERED = "registered"
    VALIDATED = "validated"
    APPROVED = "approved"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    SUSPENDED = "suspended"


class RoutingStrategy(StrEnum):
    """Deterministic model routing strategies (handbook 14.9)."""

    CAPABILITY = "capability"
    COST = "cost"
    LATENCY = "latency"
    QUALITY = "quality"
    POLICY = "policy"
    HYBRID = "hybrid"


class ResponseType(StrEnum):
    """Supported normalized response types (handbook 14.13)."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


class CostProfile(BaseModel):
    """Immutable per-1k-token cost profile for a model."""

    model_config = ConfigDict(frozen=True)

    prompt_cost_per_1k: float = 0.0
    completion_cost_per_1k: float = 0.0

    def estimate(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Return the estimated cost for the given token counts."""
        cost = (
            prompt_tokens / 1000.0 * self.prompt_cost_per_1k
            + completion_tokens / 1000.0 * self.completion_cost_per_1k
        )
        return round(cost, 6)


class ModelDescriptor(BaseModel):
    """Immutable registered-model descriptor (handbook 14.6)."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    model_id: str
    provider: str
    model_name: str
    runtime: str = "deterministic"
    version: str = "1.0.0"
    modalities: frozenset[Modality] = frozenset({Modality.TEXT})
    context_window: int = Field(default=8192, gt=0)
    max_output_tokens: int = Field(default=2048, gt=0)
    cost_profile: CostProfile = Field(default_factory=CostProfile)
    avg_latency_ms: float = 0.0
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    region: str = "local"
    compliance_tags: tuple[str, ...] = ()
    lifecycle_state: ModelLifecycleState = ModelLifecycleState.REGISTERED
    base_url: str = ""
    temperature: float = 0.0
    device: str = ""
    torch_dtype: str = ""
    system_prompt: str = ""

    @property
    def is_servable(self) -> bool:
        """Return whether the model may serve production workloads."""
        return self.lifecycle_state in (
            ModelLifecycleState.APPROVED,
            ModelLifecycleState.PRODUCTION,
        )


class ModelRequirements(BaseModel):
    """Immutable model selection requirements (handbook 14.8)."""

    model_config = ConfigDict(frozen=True)

    task_type: str = "chat"
    required_modalities: frozenset[Modality] = frozenset({Modality.TEXT})
    required_context_window: int = Field(default=0, ge=0)
    max_latency_ms: float = Field(default=0.0, ge=0.0)
    cost_ceiling: float = Field(default=0.0, ge=0.0)


class ResponseConstraints(BaseModel):
    """Immutable response constraints for a generation request."""

    model_config = ConfigDict(frozen=True)

    response_type: ResponseType = ResponseType.MARKDOWN
    max_output_tokens: int = Field(default=0, ge=0)


class TokenUsage(BaseModel):
    """Immutable token accounting for one invocation (handbook 14.14)."""

    model_config = ConfigDict(frozen=True)

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Return the total tokens consumed by the invocation."""
        return self.prompt_tokens + self.completion_tokens + self.cached_tokens


class GenerationRequest(BaseModel):
    """Immutable Model Invocation Contract input (handbook 14.10)."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    prompt_text: str = Field(min_length=1)
    tenant_id: str
    requirements: ModelRequirements = Field(default_factory=ModelRequirements)
    constraints: ResponseConstraints = Field(default_factory=ResponseConstraints)
    model_id: str | None = None
    conversation_id: str | None = None
    correlation_id: str | None = None


class NormalizedResponse(BaseModel):
    """Immutable Model Invocation Contract output (handbook 14.10, 14.13)."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    model_id: str
    provider: str
    output_text: str
    response_type: ResponseType
    token_usage: TokenUsage
    latency_ms: float
    cost_estimate: float
    finish_reason: str = "stop"
    fallback_used: bool = False
    safety_flagged: bool = False
    provider_metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StreamEventType(StrEnum):
    """Type of a streamed gateway event."""

    TOKEN = "token"  # noqa: S105 - event label, not a secret
    DONE = "done"
    ERROR = "error"


class GatewayStreamEvent(BaseModel):
    """Immutable streamed gateway event (token, done, or error)."""

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    event_type: StreamEventType
    text: str = ""
    model_id: str = ""
    finish_reason: str = ""
    token_usage: TokenUsage | None = None
    cost_estimate: float = 0.0
    error_message: str = ""

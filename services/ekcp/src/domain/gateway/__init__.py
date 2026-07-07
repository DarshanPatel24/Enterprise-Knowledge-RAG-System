"""Model management and LLM gateway domain."""

from domain.gateway.errors import (
    GatewayError,
    GatewayErrorType,
    ProviderInvocationError,
)
from domain.gateway.gateway import LLMGateway
from domain.gateway.governance import BudgetGuard, BudgetLedger
from domain.gateway.models import (
    CostProfile,
    GatewayStreamEvent,
    GenerationRequest,
    Modality,
    ModelDescriptor,
    ModelLifecycleState,
    ModelRequirements,
    NormalizedResponse,
    ResponseConstraints,
    ResponseType,
    RoutingStrategy,
    StreamEventType,
    TokenUsage,
)
from domain.gateway.policy import GatewayPolicy, ModelSettingsLike
from domain.gateway.provider import (
    ChatModelProvider,
    DeterministicEchoProvider,
    LangChainChatProvider,
    default_provider_registry,
    provider_registry_from_settings,
)
from domain.gateway.registry import (
    DETERMINISTIC_MODEL_ID,
    ModelRegistry,
    default_model_registry,
    deterministic_model,
)
from domain.gateway.selector import ModelSelector

__all__ = [
    "DETERMINISTIC_MODEL_ID",
    "BudgetGuard",
    "BudgetLedger",
    "ChatModelProvider",
    "CostProfile",
    "DeterministicEchoProvider",
    "GatewayError",
    "GatewayErrorType",
    "GatewayPolicy",
    "GatewayStreamEvent",
    "GenerationRequest",
    "LLMGateway",
    "LangChainChatProvider",
    "Modality",
    "ModelDescriptor",
    "ModelLifecycleState",
    "ModelRegistry",
    "ModelRequirements",
    "ModelSelector",
    "ModelSettingsLike",
    "NormalizedResponse",
    "ProviderInvocationError",
    "ResponseConstraints",
    "ResponseType",
    "RoutingStrategy",
    "StreamEventType",
    "TokenUsage",
    "default_model_registry",
    "default_provider_registry",
    "deterministic_model",
    "provider_registry_from_settings",
]

"""Embedding Framework (EKIE handbook Chapter 10)."""

from domain.embedding.engine import EmbeddingEngine, EmbeddingResult
from domain.embedding.errors import EmbeddingError, EmbeddingErrorType
from domain.embedding.events import EmbeddingEvent, EmbeddingEventType
from domain.embedding.model_registry import (
    EmbeddingModelRegistry,
    UnknownModelError,
    default_model_registry,
)
from domain.embedding.models import (
    DistanceMetric,
    EmbeddingDocument,
    EmbeddingModelSpec,
    EmbeddingRecord,
    EmbeddingStatus,
    ModelStatus,
)
from domain.embedding.policy import EmbeddingPolicy, EmbeddingSettingsLike
from domain.embedding.providers import (
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderRegistry,
    EmbeddingProviderSettingsLike,
    LocalHashEmbeddingProvider,
    OllamaEmbeddingProvider,
    default_provider_registry,
    provider_registry_from_settings,
)
from domain.embedding.retry import run_with_retry
from domain.embedding.selection import ModelSelectionError, ModelSelector
from domain.embedding.tokens import batched, estimate_cost, estimate_tokens
from domain.embedding.validation import (
    EmbeddingValidationErrorType,
    EmbeddingValidationReport,
    EmbeddingValidator,
)

__all__ = [
    "DistanceMetric",
    "EmbeddingDocument",
    "EmbeddingEngine",
    "EmbeddingError",
    "EmbeddingErrorType",
    "EmbeddingEvent",
    "EmbeddingEventType",
    "EmbeddingModelRegistry",
    "EmbeddingModelSpec",
    "EmbeddingPolicy",
    "EmbeddingProvider",
    "EmbeddingProviderError",
    "EmbeddingProviderRegistry",
    "EmbeddingProviderSettingsLike",
    "EmbeddingRecord",
    "EmbeddingResult",
    "EmbeddingSettingsLike",
    "EmbeddingStatus",
    "EmbeddingValidationErrorType",
    "EmbeddingValidationReport",
    "EmbeddingValidator",
    "LocalHashEmbeddingProvider",
    "ModelSelectionError",
    "ModelSelector",
    "ModelStatus",
    "OllamaEmbeddingProvider",
    "UnknownModelError",
    "batched",
    "default_model_registry",
    "default_provider_registry",
    "estimate_cost",
    "estimate_tokens",
    "provider_registry_from_settings",
    "run_with_retry",
]

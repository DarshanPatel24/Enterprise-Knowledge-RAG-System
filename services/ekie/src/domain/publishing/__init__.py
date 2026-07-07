"""Vector Publishing Framework (EKIE handbook Chapter 11)."""

from domain.publishing.cleanup import (
    DocumentDeletionResult,
    DocumentDeletionService,
    VectorCleanupError,
    VectorCleanupResult,
    VectorCleanupService,
    cleanup_provider_registry,
)
from domain.publishing.collections import CollectionResolver, CollectionSpec
from domain.publishing.engine import PublishResult, VectorPublishingEngine
from domain.publishing.errors import PublishError, PublishErrorType
from domain.publishing.events import PublishEvent, PublishEventType
from domain.publishing.identity import build_vector_id
from domain.publishing.metadata import (
    MANDATORY_METADATA_FIELDS,
    missing_required_fields,
)
from domain.publishing.models import (
    PublishedVectorSet,
    SyncState,
    VectorMetadata,
    VectorPoint,
    VectorRecord,
)
from domain.publishing.policy import PublishingPolicy, PublishingSettingsLike
from domain.publishing.providers import (
    InMemoryVectorProvider,
    QdrantConnectionLike,
    QdrantVectorProvider,
    VectorProvider,
    VectorProviderError,
    VectorProviderRegistry,
    VectorProviderSettingsLike,
    default_provider_registry,
    provider_registry_from_settings,
)
from domain.publishing.verification import (
    PublishVerifier,
    VerificationErrorType,
    VerificationReport,
)

__all__ = [
    "MANDATORY_METADATA_FIELDS",
    "CollectionResolver",
    "CollectionSpec",
    "DocumentDeletionResult",
    "DocumentDeletionService",
    "InMemoryVectorProvider",
    "VectorCleanupError",
    "VectorCleanupResult",
    "VectorCleanupService",
    "PublishError",
    "PublishErrorType",
    "PublishEvent",
    "PublishEventType",
    "PublishResult",
    "PublishVerifier",
    "PublishedVectorSet",
    "PublishingPolicy",
    "PublishingSettingsLike",
    "QdrantConnectionLike",
    "QdrantVectorProvider",
    "SyncState",
    "VectorMetadata",
    "VectorPoint",
    "VectorProvider",
    "VectorProviderError",
    "VectorProviderRegistry",
    "VectorProviderSettingsLike",
    "VectorPublishingEngine",
    "VectorRecord",
    "VerificationErrorType",
    "VerificationReport",
    "build_vector_id",
    "default_provider_registry",
    "cleanup_provider_registry",
    "missing_required_fields",
    "provider_registry_from_settings",
]

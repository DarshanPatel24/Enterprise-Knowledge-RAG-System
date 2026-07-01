"""Repository Synchronization Framework (EKIE handbook Chapters 5-6)."""

from domain.sync.change_detection import (
    ChangeDetector,
    ChangeType,
    DetectedChange,
    InventoryItem,
    TwinDocument,
)
from domain.sync.connectors import (
    ConnectorCapabilities,
    ConnectorError,
    ConnectorRegistry,
    DiscoveredObject,
    LocalFileSystemConnector,
    RepositoryConnector,
    RepositoryConnectorConfig,
    default_registry,
)
from domain.sync.events import SyncEvent, SyncEventType
from domain.sync.policy import ScanStrategy, SyncPolicy
from domain.sync.retry import RetryPolicy, run_with_retry
from domain.sync.service import (
    RepositorySynchronizer,
    SynchronizationError,
    SyncResult,
    register_repository,
)
from domain.sync.state_machine import (
    DocumentSyncState,
    InvalidStateTransitionError,
    RepositorySyncState,
    assert_document_transition,
    assert_repository_transition,
    can_transition_document,
    can_transition_repository,
)

__all__ = [
    "ChangeDetector",
    "ChangeType",
    "ConnectorCapabilities",
    "ConnectorError",
    "ConnectorRegistry",
    "DetectedChange",
    "DiscoveredObject",
    "DocumentSyncState",
    "InvalidStateTransitionError",
    "InventoryItem",
    "LocalFileSystemConnector",
    "RepositoryConnector",
    "RepositoryConnectorConfig",
    "RepositorySyncState",
    "RepositorySynchronizer",
    "RetryPolicy",
    "ScanStrategy",
    "SyncEvent",
    "SyncEventType",
    "SyncPolicy",
    "SyncResult",
    "SynchronizationError",
    "TwinDocument",
    "assert_document_transition",
    "assert_repository_transition",
    "can_transition_document",
    "can_transition_repository",
    "default_registry",
    "register_repository",
    "run_with_retry",
]

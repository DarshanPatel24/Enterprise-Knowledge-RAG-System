"""Repository connectors: abstraction, registry, and built-in adapters."""

from domain.sync.connectors.base import (
    ConnectorCapabilities,
    ConnectorError,
    DiscoveredObject,
    RepositoryConnector,
    RepositoryConnectorConfig,
)
from domain.sync.connectors.local_fs import LocalFileSystemConnector
from domain.sync.connectors.registry import (
    ConnectorFactory,
    ConnectorRegistry,
    default_registry,
)

__all__ = [
    "ConnectorCapabilities",
    "ConnectorError",
    "ConnectorFactory",
    "ConnectorRegistry",
    "DiscoveredObject",
    "LocalFileSystemConnector",
    "RepositoryConnector",
    "RepositoryConnectorConfig",
    "default_registry",
]

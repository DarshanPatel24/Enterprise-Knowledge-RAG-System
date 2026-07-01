"""Connector registration and lookup.

Repositories declare a ``connector_type``; the registry maps that type to a
factory so new connectors can be added without changing the synchronizer.
"""

from __future__ import annotations

from collections.abc import Callable

from domain.sync.connectors.base import (
    RepositoryConnector,
    RepositoryConnectorConfig,
)
from domain.sync.connectors.local_fs import LocalFileSystemConnector

ConnectorFactory = Callable[[RepositoryConnectorConfig], RepositoryConnector]


class ConnectorRegistry:
    """Maps a connector type to a factory that builds the connector."""

    def __init__(self) -> None:
        self._factories: dict[str, ConnectorFactory] = {}

    def register(self, connector_type: str, factory: ConnectorFactory) -> None:
        """Register ``factory`` under ``connector_type`` (last registration wins)."""
        self._factories[connector_type] = factory

    def create(self, config: RepositoryConnectorConfig) -> RepositoryConnector:
        """Instantiate the connector for ``config.connector_type``."""
        try:
            factory = self._factories[config.connector_type]
        except KeyError as exc:
            raise ValueError(f"no connector registered for type {config.connector_type!r}") from exc
        return factory(config)

    def registered_types(self) -> list[str]:
        """Return all registered connector types in sorted order."""
        return sorted(self._factories)


def default_registry() -> ConnectorRegistry:
    """Return a registry pre-populated with the built-in connectors."""
    registry = ConnectorRegistry()
    registry.register(LocalFileSystemConnector.connector_type, LocalFileSystemConnector)
    return registry

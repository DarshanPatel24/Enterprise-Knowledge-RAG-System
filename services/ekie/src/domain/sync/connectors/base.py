"""Repository connector abstraction.

Connectors are the only components that touch enterprise repositories. Every
downstream framework (transformation, chunking, embedding, publishing) is kept
unaware of repository implementation details, per EKIE handbook Chapter 6. A
connector discovers repository objects and reads their bytes; it does not
transform documents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ConnectorCapabilities:
    """Declares what a connector supports so the framework can adapt behavior."""

    supports_incremental: bool = True
    supports_event_notifications: bool = False


@dataclass(frozen=True)
class RepositoryConnectorConfig:
    """Configuration required to instantiate a connector for one repository."""

    repository_id: str
    tenant_id: str
    name: str
    connector_type: str
    root_uri: str


@dataclass(frozen=True)
class DiscoveredObject:
    """A single object discovered in a repository during a scan.

    ``source_path`` is normalized to forward slashes and is relative to the
    repository root, giving a stable identity independent of the host OS.
    """

    source_path: str
    name: str
    extension: str
    size_bytes: int
    modified_time: datetime
    is_hidden: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


class ConnectorError(RuntimeError):
    """Raised when a connector cannot complete a repository operation."""


class RepositoryConnector(ABC):
    """Common interface implemented by every repository connector."""

    connector_type: str

    def __init__(self, config: RepositoryConnectorConfig) -> None:
        self._config = config

    @property
    def config(self) -> RepositoryConnectorConfig:
        """Return the connector configuration."""
        return self._config

    @property
    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        """Return the capabilities advertised by this connector."""

    @abstractmethod
    def connect(self) -> None:
        """Establish and validate connectivity to the repository."""

    @abstractmethod
    def discover(self) -> Iterator[DiscoveredObject]:
        """Yield every object currently present in the repository."""

    @abstractmethod
    def read_bytes(self, source_path: str) -> bytes:
        """Return the raw bytes for ``source_path`` (used for content hashing)."""

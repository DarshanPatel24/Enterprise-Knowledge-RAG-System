"""Repository connector framework (handbook Chapter 22)."""

from domain.connectors.base import (
    Capability,
    RepositoryConnector,
    RepositoryDocument,
)
from domain.connectors.errors import ConnectorError, ConnectorErrorType
from domain.connectors.inmemory import (
    IndexedDocument,
    InMemoryRepositoryConnector,
)
from domain.connectors.qdrant import QdrantRetrievalConnector

__all__ = [
    "Capability",
    "ConnectorError",
    "ConnectorErrorType",
    "IndexedDocument",
    "InMemoryRepositoryConnector",
    "QdrantRetrievalConnector",
    "RepositoryConnector",
    "RepositoryDocument",
]

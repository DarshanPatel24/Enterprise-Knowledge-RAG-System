"""Unit tests for the Qdrant vector provider and settings-driven registry (EKIE-S6-5)."""

import importlib.util
from dataclasses import dataclass

import pytest

from domain.publishing import (
    InMemoryVectorProvider,
    QdrantVectorProvider,
    VectorProviderError,
    default_provider_registry,
    provider_registry_from_settings,
)
from domain.publishing.collections import CollectionSpec


@dataclass
class _VectorProviderSettings:
    provider: str


@dataclass
class _QdrantConnection:
    host: str = "localhost"
    port: int = 6333
    request_timeout_seconds: float = 30.0


def test_qdrant_provider_name() -> None:
    assert QdrantVectorProvider(host="localhost", port=6333).name == "qdrant"


def test_qdrant_point_id_is_deterministic() -> None:
    first = QdrantVectorProvider._point_id("enterprise_documents::CHK-000001::e1")
    second = QdrantVectorProvider._point_id("enterprise_documents::CHK-000001::e1")
    assert first == second


def test_qdrant_point_id_differs_by_vector_id() -> None:
    left = QdrantVectorProvider._point_id("enterprise_documents::CHK-000001::e1")
    right = QdrantVectorProvider._point_id("enterprise_documents::CHK-000002::e1")
    assert left != right


def test_default_registry_has_local_but_not_qdrant() -> None:
    registry = default_provider_registry()
    assert registry.get("local").name == "local"
    with pytest.raises(VectorProviderError):
        registry.get("qdrant")


def test_registry_from_settings_local_excludes_qdrant() -> None:
    registry = provider_registry_from_settings(
        _VectorProviderSettings(provider="local"), _QdrantConnection()
    )
    assert isinstance(registry.get("local"), InMemoryVectorProvider)
    with pytest.raises(VectorProviderError):
        registry.get("qdrant")


def test_registry_from_settings_selects_qdrant() -> None:
    registry = provider_registry_from_settings(
        _VectorProviderSettings(provider="qdrant"), _QdrantConnection()
    )
    assert isinstance(registry.get("qdrant"), QdrantVectorProvider)
    assert registry.get("local").name == "local"


@pytest.mark.skipif(
    importlib.util.find_spec("qdrant_client") is not None,
    reason="the 'qdrant-client' package is installed; the missing-package path is not exercised",
)
def test_qdrant_ensure_collection_without_package_raises_domain_error() -> None:
    provider = QdrantVectorProvider(host="localhost", port=6333)
    spec = CollectionSpec(name="enterprise_documents", dimension=256, distance_metric="cosine")
    with pytest.raises(VectorProviderError):
        provider.ensure_collection(spec)

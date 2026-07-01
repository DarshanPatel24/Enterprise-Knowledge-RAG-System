"""Composition root: build domain engines from environment-backed settings.

Centralizes engine construction so operational values (providers, models,
limits) come from configuration rather than code. The settings-driven provider
registries select the deterministic local providers by default and swap in real
providers (Ollama, Qdrant) only when configuration selects them, keeping the
offline path dependency-free while enabling production wiring from one place.
"""

from __future__ import annotations

from config.settings import EkieSettings
from domain.control_plane import ControlPlaneDatabase
from domain.embedding.engine import EmbeddingEngine
from domain.embedding.policy import EmbeddingPolicy
from domain.embedding.providers import (
    provider_registry_from_settings as build_embedding_provider_registry,
)
from domain.intelligence.analyzers import analyzers_from_settings
from domain.intelligence.engine import DocumentIntelligenceEngine
from domain.intelligence.policy import IntelligencePolicy
from domain.publishing.engine import VectorPublishingEngine
from domain.publishing.policy import PublishingPolicy
from domain.publishing.providers import (
    provider_registry_from_settings as build_vector_provider_registry,
)
from domain.storage import AssetStorage


def build_intelligence_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> DocumentIntelligenceEngine:
    """Build the document intelligence engine from configuration."""
    return DocumentIntelligenceEngine(
        db,
        storage,
        IntelligencePolicy.from_settings(settings.intelligence),
        analyzers=analyzers_from_settings(settings.intelligence),
    )


def build_embedding_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> EmbeddingEngine:
    """Build the embedding engine with the configured provider registry."""
    return EmbeddingEngine(
        db,
        storage,
        EmbeddingPolicy.from_settings(settings.embedding),
        provider_registry=build_embedding_provider_registry(settings.embedding),
    )


def build_publishing_engine(
    settings: EkieSettings,
    db: ControlPlaneDatabase,
    storage: AssetStorage,
) -> VectorPublishingEngine:
    """Build the vector publishing engine with the configured provider registry."""
    return VectorPublishingEngine(
        db,
        storage,
        PublishingPolicy.from_settings(settings.publishing),
        provider_registry=build_vector_provider_registry(
            settings.publishing, settings.qdrant
        ),
    )


__all__ = [
    "build_embedding_engine",
    "build_intelligence_engine",
    "build_publishing_engine",
]

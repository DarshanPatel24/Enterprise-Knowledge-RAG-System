"""Unit tests for the settings-driven composition root (EKIE-S5-5/S6-5/S3-5)."""

from composition import (
    build_embedding_engine,
    build_intelligence_engine,
    build_publishing_engine,
)
from config.settings import (
    ControlPlaneSettings,
    EkieSettings,
    EmbeddingSettings,
    IntelligenceSettings,
    PublishingSettings,
)
from domain.control_plane import ControlPlaneDatabase
from domain.embedding import EmbeddingEngine
from domain.embedding.providers import OllamaEmbeddingProvider
from domain.intelligence import DocumentIntelligenceEngine
from domain.intelligence.analyzers import LlmAnalyzer
from domain.publishing import VectorPublishingEngine
from domain.publishing.providers import QdrantVectorProvider
from domain.storage import InMemoryAssetStorage


def _db() -> ControlPlaneDatabase:
    return ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))


def test_build_engines_with_default_local_settings() -> None:
    settings = EkieSettings()
    db = _db()
    storage = InMemoryAssetStorage()
    assert isinstance(build_intelligence_engine(settings, db, storage), DocumentIntelligenceEngine)
    assert isinstance(build_embedding_engine(settings, db, storage), EmbeddingEngine)
    assert isinstance(build_publishing_engine(settings, db, storage), VectorPublishingEngine)


def test_embedding_engine_selects_ollama_provider_from_settings() -> None:
    settings = EkieSettings(embedding=EmbeddingSettings(provider="ollama"))
    engine = build_embedding_engine(settings, _db(), InMemoryAssetStorage())
    assert isinstance(engine._providers.get("ollama"), OllamaEmbeddingProvider)
    assert engine._providers.get("local").name == "local"


def test_publishing_engine_selects_qdrant_provider_from_settings() -> None:
    settings = EkieSettings(publishing=PublishingSettings(provider="qdrant"))
    engine = build_publishing_engine(settings, _db(), InMemoryAssetStorage())
    assert isinstance(engine._providers.get("qdrant"), QdrantVectorProvider)
    assert engine._providers.get("local").name == "local"


def test_intelligence_engine_appends_llm_analyzer_when_enabled() -> None:
    settings = EkieSettings(intelligence=IntelligenceSettings(enable_llm_analysis=True))
    engine = build_intelligence_engine(settings, _db(), InMemoryAssetStorage())
    assert isinstance(engine._analyzers[-1], LlmAnalyzer)


def test_intelligence_engine_excludes_llm_analyzer_by_default() -> None:
    settings = EkieSettings()
    engine = build_intelligence_engine(settings, _db(), InMemoryAssetStorage())
    assert all(analyzer.name != "llm" for analyzer in engine._analyzers)

"""Tests for the LangChain resource template and the publish/verify regression.

The template is an additive convenience/index seam. These tests exercise the
embedding-model and vector-store factories in isolation, and assert that the
existing publishing verification path is unaffected by the new module.
"""

import hashlib
import importlib.util

import pytest
from langchain_core.embeddings import Embeddings

from domain.chunking import ChunkingEngine, ChunkingPolicy
from domain.control_plane import (
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.embedding import EmbeddingEngine, EmbeddingPolicy
from domain.integrations.langchain_resources import (
    LangChainResourceError,
    build_embeddings,
    build_qdrant_vector_store,
)
from domain.intelligence import DocumentIntelligenceEngine, IntelligencePolicy
from domain.publishing import PublishingPolicy, SyncState, VectorPublishingEngine
from domain.storage import InMemoryAssetStorage
from domain.transformation import TransformationPipeline, TransformationPolicy


class _FakeEmbeddings(Embeddings):
    """A deterministic 4-dimensional embedding for hermetic vector-store tests."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[i] / 255.0 for i in range(4)]


def test_build_embeddings_rejects_local_provider() -> None:
    with pytest.raises(LangChainResourceError):
        build_embeddings("local", "local-hash-256")


def test_build_embeddings_rejects_unknown_provider() -> None:
    with pytest.raises(LangChainResourceError):
        build_embeddings("does-not-exist", "model")


@pytest.mark.skipif(
    importlib.util.find_spec("langchain_ollama") is None,
    reason="langchain-ollama is not installed",
)
def test_build_embeddings_ollama_constructs() -> None:
    embeddings = build_embeddings("ollama", "nomic-embed-text")
    assert hasattr(embeddings, "embed_documents")
    assert hasattr(embeddings, "embed_query")


@pytest.mark.skipif(
    importlib.util.find_spec("langchain_qdrant") is None,
    reason="langchain-qdrant is not installed",
)
def test_build_qdrant_vector_store_roundtrip_in_memory() -> None:
    store = build_qdrant_vector_store(
        _FakeEmbeddings(),
        collection="template_test",
        location=":memory:",
        vector_size=4,
        create_collection=True,
    )
    store.add_texts(
        ["disconnect power before service", "inspect the seals"],
        metadatas=[{"src": "a"}, {"src": "b"}],
    )
    results = store.similarity_search("disconnect power before service", k=1)
    assert len(results) >= 1
    assert results[0].page_content in {
        "disconnect power before service",
        "inspect the seals",
    }


_MARKDOWN = """# Equipment Maintenance

Overview of the maintenance workflow for the pump station.

## Safety

Warning: disconnect power before service.

## Inspection

1. Inspect the seals.
2. Check the pressure gauge.
"""


def _prepare_to_embeddings(db: ControlPlaneDatabase) -> tuple[str, InMemoryAssetStorage]:
    with db.session() as session:
        repo = Repository(
            tenant_id="tenant-a",
            name="repo",
            source_type="local_fs",
            uri="local://repo",
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repo)
        session.flush()
        document = Document(
            repository_id=repo.id,
            tenant_id="tenant-a",
            source_path="docs/maint.md",
            content_hash="hash-maint",
            classification_clearance="internal",
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        document_id = document.id
    storage = InMemoryAssetStorage()
    TransformationPipeline(db, storage, TransformationPolicy()).transform(
        document_id, "tenant-a", _MARKDOWN.encode("utf-8")
    )
    DocumentIntelligenceEngine(db, storage, IntelligencePolicy()).enrich(
        document_id, "tenant-a"
    )
    ChunkingEngine(db, storage, ChunkingPolicy()).chunk(document_id, "tenant-a")
    EmbeddingEngine(db, storage, EmbeddingPolicy()).embed(document_id, "tenant-a")
    return document_id, storage


def test_publishing_verification_path_unaffected_by_template(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    # Importing the LangChain template must not change the verified publish path.
    document_id, storage = _prepare_to_embeddings(control_plane_db)
    engine = VectorPublishingEngine(control_plane_db, storage, PublishingPolicy())

    result = engine.publish(document_id, "tenant-a")

    assert result.created is True
    assert result.vector_count >= 3
    assert result.verified_count == result.vector_count
    assert all(
        record.state is SyncState.VERIFIED
        for record in result.published_vector_set.records
    )

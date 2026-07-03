"""Tests for publishing collection resolution strategies."""

from __future__ import annotations

from domain.control_plane import Document
from domain.embedding.models import DistanceMetric, EmbeddingDocument
from domain.publishing.collections import CollectionResolver
from domain.publishing.policy import PublishingPolicy


def _document() -> Document:
    return Document(
        id="doc-1",
        repository_id="repo-1",
        tenant_id="tenant-a",
        source_path="docs/a.md",
        content_hash="seed",
        classification_clearance="internal",
        version=1,
    )


def _embedding() -> EmbeddingDocument:
    return EmbeddingDocument(
        document_id="doc-1",
        source_markdown_version=1,
        model_name="Qwen/Qwen3-VL-Embedding-8B",
        provider="huggingface",
        dimension=4096,
        distance_metric=DistanceMetric.COSINE,
        embedding_count=1,
        total_tokens=10,
        records=[],
    )


def test_static_collection_strategy_keeps_default_name() -> None:
    resolver = CollectionResolver(
        PublishingPolicy(default_collection="enterprise_documents")
    )

    spec = resolver.resolve(_document(), _embedding())

    assert spec.name == "enterprise_documents"
    assert spec.dimension == 4096
    assert spec.distance_metric == "cosine"


def test_model_scoped_collection_strategy_includes_model_and_dimension() -> None:
    resolver = CollectionResolver(
        PublishingPolicy(
            default_collection="enterprise_documents",
            collection_strategy="model_scoped",
        )
    )

    spec = resolver.resolve(_document(), _embedding())

    assert spec.name == (
        "enterprise_documents__huggingface__"
        "qwen_qwen3_vl_embedding_8b__d4096"
    )

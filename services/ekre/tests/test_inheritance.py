"""Tests for embedding + distance metric inheritance from EKIE metadata."""

from __future__ import annotations

import pytest

from contracts.enums import DistanceMetric
from domain.inheritance import (
    CollectionSchema,
    InheritanceError,
    InheritanceErrorType,
    InheritanceResolver,
)


class _FakeReader:
    def __init__(self, schema: CollectionSchema) -> None:
        self._schema = schema

    def read(self, collection: str) -> CollectionSchema:
        return self._schema


def test_fully_inherited_profile() -> None:
    reader = _FakeReader(
        CollectionSchema(
            collection="enterprise_documents",
            dimension=1024,
            distance_metric=DistanceMetric.COSINE,
            embedding_model="ekie-model-a",
            embedding_version=3,
        )
    )
    resolver = InheritanceResolver(reader)
    profile = resolver.resolve("enterprise_documents")
    assert profile.embedding_model == "ekie-model-a"
    assert profile.dimension == 1024
    assert profile.distance_metric is DistanceMetric.COSINE
    assert profile.embedding_version == 3
    assert profile.source == "inherited"


def test_hybrid_uses_schema_metric_and_payload_model() -> None:
    # Metric + dimension from schema, model resolved -> hybrid source when either
    # side is absent but recoverable is exercised via fallback below.
    reader = _FakeReader(
        CollectionSchema(
            collection="c",
            dimension=512,
            distance_metric=DistanceMetric.DOT_PRODUCT,
            embedding_model=None,
        )
    )
    resolver = InheritanceResolver(
        reader,
        allow_config_fallback=True,
        fallback_embedding_model="fallback-model",
    )
    profile = resolver.resolve("c")
    assert profile.embedding_model == "fallback-model"
    assert profile.distance_metric is DistanceMetric.DOT_PRODUCT
    assert profile.source == "hybrid"


def test_fallback_supplies_missing_dimension() -> None:
    reader = _FakeReader(
        CollectionSchema(
            collection="c",
            dimension=None,
            distance_metric=DistanceMetric.COSINE,
            embedding_model="m",
        )
    )
    resolver = InheritanceResolver(
        reader, allow_config_fallback=True, fallback_dimension=768
    )
    profile = resolver.resolve("c")
    assert profile.dimension == 768


def test_unresolved_dimension_without_fallback_raises() -> None:
    reader = _FakeReader(
        CollectionSchema(
            collection="c",
            dimension=None,
            distance_metric=DistanceMetric.COSINE,
            embedding_model="m",
        )
    )
    resolver = InheritanceResolver(reader, allow_config_fallback=False)
    with pytest.raises(InheritanceError) as exc:
        resolver.resolve("c")
    assert exc.value.error_type is InheritanceErrorType.DIMENSION_UNRESOLVED


def test_unresolved_model_without_fallback_raises() -> None:
    reader = _FakeReader(
        CollectionSchema(
            collection="c",
            dimension=256,
            distance_metric=DistanceMetric.COSINE,
            embedding_model=None,
        )
    )
    resolver = InheritanceResolver(reader, allow_config_fallback=False)
    with pytest.raises(InheritanceError) as exc:
        resolver.resolve("c")
    assert exc.value.error_type is InheritanceErrorType.MODEL_UNRESOLVED

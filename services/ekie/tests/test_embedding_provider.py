"""Unit tests for embedding providers (determinism and shape)."""

import math

from domain.embedding import LocalHashEmbeddingProvider


def test_local_provider_is_deterministic() -> None:
    provider = LocalHashEmbeddingProvider()

    first = provider.embed(["hello world"], dimension=16, normalize=False)
    second = provider.embed(["hello world"], dimension=16, normalize=False)

    assert first == second


def test_local_provider_respects_dimension() -> None:
    provider = LocalHashEmbeddingProvider()

    vectors = provider.embed(["a", "b", "c"], dimension=32, normalize=False)

    assert len(vectors) == 3
    assert all(len(vector) == 32 for vector in vectors)


def test_local_provider_normalizes_to_unit_length() -> None:
    provider = LocalHashEmbeddingProvider()

    [vector] = provider.embed(["knowledge base"], dimension=64, normalize=True)

    magnitude = math.sqrt(sum(value * value for value in vector))
    assert math.isclose(magnitude, 1.0, rel_tol=1e-9)


def test_local_provider_distinct_inputs_differ() -> None:
    provider = LocalHashEmbeddingProvider()

    [left] = provider.embed(["alpha"], dimension=16, normalize=False)
    [right] = provider.embed(["beta"], dimension=16, normalize=False)

    assert left != right

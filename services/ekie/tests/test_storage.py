"""Tests for the immutable versioned asset storage abstraction."""

import pytest

from domain.storage import (
    AssetAlreadyExistsError,
    AssetNotFoundError,
    InMemoryAssetStorage,
    compute_content_hash,
)


def test_put_and_get_roundtrip() -> None:
    storage = InMemoryAssetStorage()
    stored = storage.put("doc-1/markdown", b"# Title", version=1)
    assert stored.version == 1
    assert stored.size_bytes == len(b"# Title")
    assert stored.content_hash == compute_content_hash(b"# Title")
    assert storage.get("doc-1/markdown", version=1) == b"# Title"


def test_immutability_is_enforced() -> None:
    storage = InMemoryAssetStorage()
    storage.put("doc-1/markdown", b"v1", version=1)
    with pytest.raises(AssetAlreadyExistsError):
        storage.put("doc-1/markdown", b"v1-overwrite", version=1)


def test_versioning_and_latest() -> None:
    storage = InMemoryAssetStorage()
    storage.put_next("doc-1/chunks", b"a")
    storage.put_next("doc-1/chunks", b"b")
    assert storage.list_versions("doc-1/chunks") == [1, 2]
    assert storage.latest_version("doc-1/chunks") == 2
    assert storage.get("doc-1/chunks", version=2) == b"b"


def test_missing_asset_raises() -> None:
    storage = InMemoryAssetStorage()
    assert storage.latest_version("absent") is None
    with pytest.raises(AssetNotFoundError):
        storage.get("absent", version=1)

"""Tests for the persistent filesystem-backed asset storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.storage import (
    AssetAlreadyExistsError,
    AssetNotFoundError,
    LocalFileAssetStorage,
)


def test_put_and_get_roundtrip(tmp_path: Path) -> None:
    store = LocalFileAssetStorage(tmp_path / "assets")
    stored = store.put("tenant-a/doc-1/markdown", b"# hello", version=1)

    assert stored.version == 1
    assert stored.size_bytes == len(b"# hello")
    assert store.get("tenant-a/doc-1/markdown", version=1) == b"# hello"


def test_assets_survive_a_new_instance(tmp_path: Path) -> None:
    root = tmp_path / "assets"
    LocalFileAssetStorage(root).put("tenant-a/doc-1/markdown", b"payload", version=1)

    # A fresh instance (simulating a process/worker restart) still reads it.
    reopened = LocalFileAssetStorage(root)
    assert reopened.get("tenant-a/doc-1/markdown", version=1) == b"payload"
    assert reopened.latest_version("tenant-a/doc-1/markdown") == 1


def test_put_next_increments_versions(tmp_path: Path) -> None:
    store = LocalFileAssetStorage(tmp_path / "assets")
    first = store.put_next("k", b"v1")
    second = store.put_next("k", b"v2")

    assert (first.version, second.version) == (1, 2)
    assert store.list_versions("k") == [1, 2]
    assert store.latest_version("k") == 2
    assert store.get("k", version=1) == b"v1"
    assert store.get("k", version=2) == b"v2"


def test_writes_are_immutable(tmp_path: Path) -> None:
    store = LocalFileAssetStorage(tmp_path / "assets")
    store.put("k", b"first", version=1)

    with pytest.raises(AssetAlreadyExistsError):
        store.put("k", b"second", version=1)
    assert store.get("k", version=1) == b"first"


def test_get_missing_raises(tmp_path: Path) -> None:
    store = LocalFileAssetStorage(tmp_path / "assets")
    with pytest.raises(AssetNotFoundError):
        store.get("nope", version=1)


def test_head_returns_metadata_and_missing_raises(tmp_path: Path) -> None:
    store = LocalFileAssetStorage(tmp_path / "assets")
    store.put("k", b"data", version=1)

    head = store.head("k", version=1)
    assert head.key == "k"
    assert head.version == 1
    assert head.size_bytes == 4

    with pytest.raises(AssetNotFoundError):
        store.head("k", version=2)


def test_head_reconstructs_when_sidecar_missing(tmp_path: Path) -> None:
    root = tmp_path / "assets"
    store = LocalFileAssetStorage(root)
    store.put("tenant/doc/markdown", b"data", version=1)

    # Remove the metadata sidecar; head must still work from the payload.
    for meta in (root / "tenant" / "doc" / "markdown").glob("*.meta.json"):
        meta.unlink()

    head = store.head("tenant/doc/markdown", version=1)
    assert head.version == 1
    assert head.size_bytes == 4


def test_nested_keys_map_to_subdirectories(tmp_path: Path) -> None:
    root = tmp_path / "assets"
    store = LocalFileAssetStorage(root)
    store.put("tenant-a/doc-1/vectors", b"x", version=1)

    assert (root / "tenant-a" / "doc-1" / "vectors" / "v000001.bin").is_file()


def test_list_versions_empty_for_unknown_key(tmp_path: Path) -> None:
    store = LocalFileAssetStorage(tmp_path / "assets")
    assert store.list_versions("missing") == []
    assert store.latest_version("missing") is None

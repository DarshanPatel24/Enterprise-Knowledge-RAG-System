"""Filesystem-backed immutable versioned asset storage.

Implements the :class:`AssetStorage` contract using a local directory tree so
generated pipeline assets survive process restarts without requiring an object
store (MinIO). This is the default local-first backend: it keeps enterprise data
on the local machine while guaranteeing that stage payloads (markdown, chunks,
embeddings, vectors) remain readable after a worker or API restart.

Layout under the configured root directory mirrors the MinIO scheme::

    <root>/<key>/v000001.bin        -- binary asset payload
    <root>/<key>/v000001.meta.json  -- JSON-serialised StoredAsset metadata

``<key>`` may contain ``/`` separators (e.g. ``tenant/document/markdown``); each
segment maps to a subdirectory. Writes are atomic (temp file + rename) and
immutable: re-writing an existing ``(key, version)`` raises.
"""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from domain.storage.base import (
    AssetAlreadyExistsError,
    AssetNotFoundError,
    AssetStorage,
    StoredAsset,
    compute_content_hash,
)

# Characters that are unsafe in path segments on common filesystems (notably
# Windows). Key segments are slugs/UUIDs/stage names in practice, so replacing
# any stray unsafe character keeps paths valid without realistic collisions.
_UNSAFE = re.compile(r'[<>:"|?*\x00-\x1f]')


def _sanitize_segment(segment: str) -> str:
    cleaned = _UNSAFE.sub("_", segment).strip().rstrip(".")
    return cleaned or "_"


class LocalFileAssetStorage(AssetStorage):
    """Local directory implementation of :class:`AssetStorage`.

    Persists assets under ``root`` so they outlive the process. Suitable for
    single-node local deployments; for multi-node use a shared object store
    (:class:`MinIOAssetStorage`).
    """

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _key_dir(self, key: str) -> Path:
        segments = [
            _sanitize_segment(part)
            for part in key.replace("\\", "/").split("/")
            if part
        ]
        return self._root.joinpath(*segments)

    @staticmethod
    def _blob_name(version: int) -> str:
        return f"v{version:06d}.bin"

    @staticmethod
    def _meta_name(version: int) -> str:
        return f"v{version:06d}.meta.json"

    def put(self, key: str, data: bytes, *, version: int) -> StoredAsset:
        directory = self._key_dir(key)
        directory.mkdir(parents=True, exist_ok=True)
        blob_path = directory / self._blob_name(version)
        meta_path = directory / self._meta_name(version)
        if blob_path.exists():
            raise AssetAlreadyExistsError(
                f"asset {key!r} version {version} already exists"
            )
        asset = StoredAsset(
            key=key,
            version=version,
            content_hash=compute_content_hash(data),
            size_bytes=len(data),
            created_at=datetime.now(UTC),
        )
        # Atomic publish: write to a temp file then rename so a crash never
        # leaves a partially written asset that would read as valid.
        tmp_path = directory / f".{self._blob_name(version)}.{os.getpid()}.tmp"
        tmp_path.write_bytes(data)
        os.replace(tmp_path, blob_path)
        meta_path.write_text(
            json.dumps(
                {
                    "key": asset.key,
                    "version": asset.version,
                    "content_hash": asset.content_hash,
                    "size_bytes": asset.size_bytes,
                    "created_at": asset.created_at.isoformat(),
                }
            ),
            encoding="utf-8",
        )
        return asset

    def get(self, key: str, *, version: int) -> bytes:
        blob_path = self._key_dir(key) / self._blob_name(version)
        try:
            return blob_path.read_bytes()
        except FileNotFoundError as exc:
            raise AssetNotFoundError(
                f"asset {key!r} version {version} not found"
            ) from exc

    def head(self, key: str, *, version: int) -> StoredAsset:
        directory = self._key_dir(key)
        blob_path = directory / self._blob_name(version)
        if not blob_path.exists():
            raise AssetNotFoundError(f"asset {key!r} version {version} not found")
        meta_path = directory / self._meta_name(version)
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            return StoredAsset(
                key=meta["key"],
                version=int(meta["version"]),
                content_hash=meta["content_hash"],
                size_bytes=int(meta["size_bytes"]),
                created_at=datetime.fromisoformat(meta["created_at"]),
            )
        except (FileNotFoundError, ValueError, KeyError):
            # Reconstruct metadata from the payload if the sidecar is missing.
            data = blob_path.read_bytes()
            stat = blob_path.stat()
            return StoredAsset(
                key=key,
                version=version,
                content_hash=compute_content_hash(data),
                size_bytes=len(data),
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            )

    def latest_version(self, key: str) -> int | None:
        versions = self.list_versions(key)
        return versions[-1] if versions else None

    def list_versions(self, key: str) -> list[int]:
        directory = self._key_dir(key)
        if not directory.is_dir():
            return []
        versions: list[int] = []
        for entry in directory.iterdir():
            name = entry.name
            if name.startswith("v") and name.endswith(".bin"):
                try:
                    versions.append(int(name[1:-4]))
                except ValueError:
                    continue
        return sorted(versions)

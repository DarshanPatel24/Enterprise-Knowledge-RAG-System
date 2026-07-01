"""Immutable, versioned asset storage abstraction.

Defines the storage contract every ingestion stage uses to persist generated
assets. The contract guarantees immutability: once a ``(key, version)`` pair is
written it can never be overwritten. Content addressing (SHA-256) supports
deterministic verification and lineage.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime


class AssetAlreadyExistsError(RuntimeError):
    """Raised when attempting to overwrite an existing immutable asset version."""


class AssetNotFoundError(KeyError):
    """Raised when a requested asset version does not exist."""


@dataclass(frozen=True)
class StoredAsset:
    """Metadata describing a persisted immutable asset version."""

    key: str
    version: int
    content_hash: str
    size_bytes: int
    created_at: datetime


def compute_content_hash(data: bytes) -> str:
    """Return the SHA-256 hex digest for ``data``."""
    return hashlib.sha256(data).hexdigest()


class AssetStorage(ABC):
    """Contract for immutable, versioned asset persistence."""

    @abstractmethod
    def put(self, key: str, data: bytes, *, version: int) -> StoredAsset:
        """Persist ``data`` under ``key`` at ``version``.

        Implementations must reject any write to an existing ``(key, version)``
        pair by raising :class:`AssetAlreadyExistsError`.
        """

    @abstractmethod
    def get(self, key: str, *, version: int) -> bytes:
        """Return the bytes stored for ``key`` at ``version``."""

    @abstractmethod
    def head(self, key: str, *, version: int) -> StoredAsset:
        """Return metadata for ``key`` at ``version`` without the payload."""

    @abstractmethod
    def latest_version(self, key: str) -> int | None:
        """Return the highest stored version for ``key`` or ``None``."""

    @abstractmethod
    def list_versions(self, key: str) -> list[int]:
        """Return all stored versions for ``key`` in ascending order."""

    def put_next(self, key: str, data: bytes) -> StoredAsset:
        """Persist ``data`` as the next sequential version for ``key``."""
        current = self.latest_version(key)
        next_version = 1 if current is None else current + 1
        return self.put(key, data, version=next_version)


class InMemoryAssetStorage(AssetStorage):
    """In-memory implementation of :class:`AssetStorage` for tests and local use."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, int], bytes] = {}
        self._meta: dict[tuple[str, int], StoredAsset] = {}

    def put(self, key: str, data: bytes, *, version: int) -> StoredAsset:
        composite = (key, version)
        if composite in self._data:
            raise AssetAlreadyExistsError(f"asset {key!r} version {version} already exists")
        asset = StoredAsset(
            key=key,
            version=version,
            content_hash=compute_content_hash(data),
            size_bytes=len(data),
            created_at=datetime.now(UTC),
        )
        self._data[composite] = data
        self._meta[composite] = asset
        return asset

    def get(self, key: str, *, version: int) -> bytes:
        try:
            return self._data[(key, version)]
        except KeyError as exc:
            raise AssetNotFoundError(f"asset {key!r} version {version} not found") from exc

    def head(self, key: str, *, version: int) -> StoredAsset:
        try:
            return self._meta[(key, version)]
        except KeyError as exc:
            raise AssetNotFoundError(f"asset {key!r} version {version} not found") from exc

    def latest_version(self, key: str) -> int | None:
        versions = self.list_versions(key)
        return versions[-1] if versions else None

    def list_versions(self, key: str) -> list[int]:
        return sorted(version for stored_key, version in self._data if stored_key == key)

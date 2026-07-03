"""MinIO-backed immutable versioned asset storage.

Implements the :class:`AssetStorage` contract using a self-hosted MinIO
object store so that generated pipeline assets survive service restarts.
Each ``(key, version)`` pair maps to a deterministic object path under the
configured bucket; the scheme enforces immutability at write time.

This implementation is selected by the composition root when
``EKIE_STORAGE__ENDPOINT`` is non-empty and ``EKIE_ENVIRONMENT != local``.
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from domain.storage.base import (
    AssetAlreadyExistsError,
    AssetNotFoundError,
    AssetStorage,
    StoredAsset,
    compute_content_hash,
)

if TYPE_CHECKING:
    from minio import Minio


def _object_name(key: str, version: int) -> str:
    """Return the canonical MinIO object name for a ``(key, version)`` pair."""
    return f"{key}/v{version:06d}"


def _meta_object_name(key: str, version: int) -> str:
    """Return the metadata sidecar object name for a ``(key, version)`` pair."""
    return f"{key}/v{version:06d}.meta.json"


class MinIOAssetStorage(AssetStorage):
    """MinIO-backed implementation of :class:`AssetStorage` (handbook 14).

    The storage layout inside the configured bucket:
    - ``<key>/v000001``          — binary asset payload
    - ``<key>/v000001.meta.json`` — JSON-serialised :class:`StoredAsset` metadata
    """

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        try:
            from minio import Minio as _Minio
        except ImportError as exc:
            raise RuntimeError(
                "MinIOAssetStorage requires the 'minio' package. "
                "Install it with: pip install -e 'services/ekie[storage]'"
            ) from exc
        self._client: Minio = _Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create the bucket if it does not already exist."""
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def put(self, key: str, data: bytes, *, version: int) -> StoredAsset:
        """Persist ``data`` under ``key`` at ``version``, rejecting overwrites."""
        obj_name = _object_name(key, version)
        # Immutability check — stat the object; if it exists, reject.
        try:
            self._client.stat_object(self._bucket, obj_name)
            raise AssetAlreadyExistsError(
                f"asset {key!r} version {version} already exists"
            )
        except Exception as exc:
            if isinstance(exc, AssetAlreadyExistsError):
                raise
            # stat raises an S3Error with code "NoSuchKey" when absent — proceed.

        content_hash = compute_content_hash(data)
        created_at = datetime.now(UTC)
        asset = StoredAsset(
            key=key,
            version=version,
            content_hash=content_hash,
            size_bytes=len(data),
            created_at=created_at,
        )

        # Upload payload.
        self._client.put_object(
            self._bucket,
            obj_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type="application/octet-stream",
        )

        # Upload metadata sidecar.
        meta_bytes = json.dumps(
            {
                "key": asset.key,
                "version": asset.version,
                "content_hash": asset.content_hash,
                "size_bytes": asset.size_bytes,
                "created_at": asset.created_at.isoformat(),
            }
        ).encode("utf-8")
        self._client.put_object(
            self._bucket,
            _meta_object_name(key, version),
            data=io.BytesIO(meta_bytes),
            length=len(meta_bytes),
            content_type="application/json",
        )
        return asset

    def get(self, key: str, *, version: int) -> bytes:
        """Return the bytes stored for ``key`` at ``version``."""
        obj_name = _object_name(key, version)
        try:
            response = self._client.get_object(self._bucket, obj_name)
            return response.read()
        except Exception as exc:
            raise AssetNotFoundError(
                f"asset {key!r} version {version} not found"
            ) from exc
        finally:
            try:
                response.close()  # type: ignore[union-attr]
                response.release_conn()  # type: ignore[union-attr]
            except Exception:
                pass

    def head(self, key: str, *, version: int) -> StoredAsset:
        """Return metadata for ``key`` at ``version`` without the payload."""
        meta_name = _meta_object_name(key, version)
        try:
            response = self._client.get_object(self._bucket, meta_name)
            meta = json.loads(response.read())
        except Exception as exc:
            raise AssetNotFoundError(
                f"asset {key!r} version {version} not found"
            ) from exc
        finally:
            try:
                response.close()  # type: ignore[union-attr]
                response.release_conn()  # type: ignore[union-attr]
            except Exception:
                pass
        return StoredAsset(
            key=meta["key"],
            version=meta["version"],
            content_hash=meta["content_hash"],
            size_bytes=meta["size_bytes"],
            created_at=datetime.fromisoformat(meta["created_at"]),
        )

    def latest_version(self, key: str) -> int | None:
        """Return the highest stored version for ``key`` or ``None``."""
        versions = self.list_versions(key)
        return versions[-1] if versions else None

    def list_versions(self, key: str) -> list[int]:
        """Return all stored versions for ``key`` in ascending order."""
        prefix = f"{key}/v"
        versions: list[int] = []
        for obj in self._client.list_objects(self._bucket, prefix=prefix):
            name = obj.object_name or ""
            # Only count payload objects, not sidecar .meta.json files.
            if name.endswith(".meta.json"):
                continue
            try:
                version_str = name[len(prefix):]
                versions.append(int(version_str))
            except ValueError:
                continue
        return sorted(versions)

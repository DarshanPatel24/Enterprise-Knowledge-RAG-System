"""Vector cleanup service for source-deletion propagation.

When a source file is deleted, the document twin is marked deleted in the
Control Plane. This service additionally removes published vectors from the
active vector provider (for example Qdrant) using the stored published-vector
asset payload.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.control_plane import Asset, AssetType, ControlPlaneDatabase
from domain.publishing.models import PublishedVectorSet
from domain.publishing.providers import (
    InMemoryVectorProvider,
    QdrantVectorProvider,
    VectorProviderError,
    VectorProviderRegistry,
)
from domain.storage import AssetStorage


class VectorCleanupError(RuntimeError):
    """Raised when vector cleanup cannot complete."""


@dataclass(frozen=True)
class VectorCleanupResult:
    """Outcome of deleting vectors for one deleted document."""

    document_id: str
    tenant_id: str
    provider: str
    collection: str
    deleted_count: int


@dataclass(frozen=True)
class _VectorAssetRef:
    version: int
    content: str


class VectorCleanupService:
    """Removes published vectors for a deleted document."""

    def __init__(
        self,
        db: ControlPlaneDatabase,
        storage: AssetStorage,
        provider_registry: VectorProviderRegistry,
    ) -> None:
        self._db = db
        self._storage = storage
        self._providers = provider_registry

    def purge_document_vectors(
        self, document_id: str, tenant_id: str
    ) -> VectorCleanupResult | None:
        """Delete vectors associated with a document's latest vector asset.

        Returns ``None`` when no vector asset exists (already clean / never
        published).
        """
        ref = self._load_vector_asset(document_id, tenant_id)
        if ref is None:
            return None

        try:
            published = PublishedVectorSet.model_validate_json(ref.content)
        except Exception as exc:
            raise VectorCleanupError(
                f"invalid vector payload for document {document_id!r}: {exc}"
            ) from exc

        vector_ids = [record.vector_id for record in published.records]
        if not vector_ids:
            return VectorCleanupResult(
                document_id=document_id,
                tenant_id=tenant_id,
                provider=published.provider,
                collection=published.collection,
                deleted_count=0,
            )

        try:
            provider = self._providers.get(published.provider)
            provider.delete(published.collection, vector_ids)
        except VectorProviderError as exc:
            raise VectorCleanupError(str(exc)) from exc

        return VectorCleanupResult(
            document_id=document_id,
            tenant_id=tenant_id,
            provider=published.provider,
            collection=published.collection,
            deleted_count=len(vector_ids),
        )

    def _load_vector_asset(self, document_id: str, tenant_id: str) -> _VectorAssetRef | None:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(
                    Asset.document_id == document_id,
                    Asset.tenant_id == tenant_id,
                    Asset.asset_type == AssetType.VECTOR,
                )
                .order_by(Asset.version.desc())
                .first()
            )
            version = asset.version if asset is not None else None
        if version is None:
            return None

        key = f"{tenant_id}/{document_id}/vectors"
        try:
            payload = self._storage.get(key, version=version).decode("utf-8")
        except (KeyError, OSError) as exc:
            raise VectorCleanupError(
                f"vector payload unavailable for deleted document {document_id!r}"
            ) from exc
        return _VectorAssetRef(version=version, content=payload)


def cleanup_provider_registry(
    *,
    qdrant_host: str,
    qdrant_port: int,
    qdrant_timeout_seconds: float,
) -> VectorProviderRegistry:
    """Build a registry suitable for deletion from local or qdrant providers."""
    return VectorProviderRegistry(
        [
            InMemoryVectorProvider(),
            QdrantVectorProvider(
                host=qdrant_host,
                port=qdrant_port,
                request_timeout_seconds=qdrant_timeout_seconds,
            ),
        ]
    )

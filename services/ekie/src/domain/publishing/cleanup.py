"""Vector cleanup service for source-deletion propagation.

When a source file is deleted, the document twin is marked deleted in the
Control Plane. This service additionally removes published vectors from the
active vector provider (for example Qdrant) using the stored published-vector
asset payload.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_

from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    IngestionJob,
    IngestionSource,
    JobKind,
    Lineage,
)
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
class DocumentDeletionResult:
    """Outcome of hard-deleting a document from the Control Plane."""

    document_id: str
    tenant_id: str
    vectors_deleted: int
    row_deleted: bool
    provider: str | None = None
    collection: str | None = None
    vector_cleanup_error: str | None = None


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
        *,
        fallback_provider: str | None = None,
        fallback_collection: str | None = None,
    ) -> None:
        self._db = db
        self._storage = storage
        self._providers = provider_registry
        # When the published manifest is unavailable, these let cleanup fall back
        # to a metadata-filter delete against the configured vector store so
        # orphaned vectors are still reclaimed (see purge_document_vectors).
        self._fallback_provider = fallback_provider
        self._fallback_collection = fallback_collection

    def purge_document_vectors(
        self, document_id: str, tenant_id: str
    ) -> VectorCleanupResult | None:
        """Delete vectors associated with a document.

        Prefers the published manifest (precise, by vector identity). When the
        manifest is missing or unreadable it falls back to a metadata-filter
        delete against the configured vector store, so vectors are reclaimed even
        if the manifest was lost. Returns ``None`` only when nothing could be
        cleaned and no fallback is configured.
        """
        try:
            ref = self._load_vector_asset(document_id, tenant_id)
        except VectorCleanupError:
            # Manifest row exists but its payload is gone; fall back to a filter
            # delete when possible, otherwise preserve the original error.
            fallback = self._purge_by_filter(document_id, tenant_id)
            if fallback is not None:
                return fallback
            raise

        if ref is None:
            return self._purge_by_filter(document_id, tenant_id)

        try:
            published = PublishedVectorSet.model_validate_json(ref.content)
        except Exception as exc:
            fallback = self._purge_by_filter(document_id, tenant_id)
            if fallback is not None:
                return fallback
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

    def _purge_by_filter(
        self, document_id: str, tenant_id: str
    ) -> VectorCleanupResult | None:
        """Delete a document's vectors by metadata filter, if a fallback is set."""
        if self._fallback_provider is None or self._fallback_collection is None:
            return None
        try:
            provider = self._providers.get(self._fallback_provider)
            deleted = provider.delete_by_document(
                self._fallback_collection, tenant_id, document_id
            )
        except VectorProviderError as exc:
            raise VectorCleanupError(str(exc)) from exc
        return VectorCleanupResult(
            document_id=document_id,
            tenant_id=tenant_id,
            provider=self._fallback_provider,
            collection=self._fallback_collection,
            deleted_count=deleted,
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


class DocumentDeletionService:
    """Hard-deletes a document: purges its vectors, then removes Control Plane rows.

    Deleting the ``Document`` row cascades to its assets, workflows, and
    processing-state records. Vectors live outside the Control Plane (in the
    vector provider) and must be purged first, while the vector-asset payload is
    still resolvable, to avoid orphaning them.
    """

    def __init__(
        self, db: ControlPlaneDatabase, vector_cleanup: VectorCleanupService
    ) -> None:
        self._db = db
        self._vectors = vector_cleanup

    def delete_document(
        self, document_id: str, tenant_id: str, *, force: bool = False
    ) -> DocumentDeletionResult:
        """Purge a document's vectors and delete its Control Plane rows.

        When ``force`` is ``False`` a vector-cleanup failure aborts the deletion
        (so it can be retried safely). When ``force`` is ``True`` the row is
        removed regardless, recording the cleanup error for visibility.
        """
        vectors_deleted = 0
        provider: str | None = None
        collection: str | None = None
        cleanup_error: str | None = None

        try:
            result = self._vectors.purge_document_vectors(document_id, tenant_id)
            if result is not None:
                vectors_deleted = result.deleted_count
                provider = result.provider
                collection = result.collection
        except VectorCleanupError as exc:
            if not force:
                raise
            cleanup_error = str(exc)

        row_deleted = self._delete_row(document_id, tenant_id)
        return DocumentDeletionResult(
            document_id=document_id,
            tenant_id=tenant_id,
            vectors_deleted=vectors_deleted,
            row_deleted=row_deleted,
            provider=provider,
            collection=collection,
            vector_cleanup_error=cleanup_error,
        )

    def _delete_row(self, document_id: str, tenant_id: str) -> bool:
        with self._db.session() as session:
            # Ingestion jobs and staged sources are intentionally FK-free (a
            # delete job can outlive its document), so they are not cascade-
            # deleted. Purge the document's pending ingest jobs and staged
            # source unconditionally -- even when the document row is already
            # gone -- so a delete never leaves orphaned work that would later
            # dead-letter and require manual cleanup.
            session.query(IngestionJob).filter(
                IngestionJob.tenant_id == tenant_id,
                IngestionJob.document_id == document_id,
                IngestionJob.kind == JobKind.INGEST,
            ).delete()
            session.query(IngestionSource).filter(
                IngestionSource.tenant_id == tenant_id,
                IngestionSource.document_id == document_id,
            ).delete()
            document = session.get(Document, document_id)
            if document is None or document.tenant_id != tenant_id:
                return False
            session.delete(document)
            return True


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

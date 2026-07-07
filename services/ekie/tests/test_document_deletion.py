"""Tests for hard-deleting documents via :class:`DocumentDeletionService`."""

from __future__ import annotations

from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    ProcessingState,
    Repository,
    Workflow,
)
from domain.publishing import (
    DocumentDeletionService,
    PublishedVectorSet,
    SyncState,
    VectorCleanupService,
    VectorMetadata,
    VectorPoint,
    VectorProviderRegistry,
    VectorRecord,
)
from domain.publishing.collections import CollectionSpec
from domain.publishing.providers.local import InMemoryVectorProvider
from domain.storage import AssetStorage, InMemoryAssetStorage

_TENANT = "tenant-del"
_COLLECTION = "enterprise_documents"


def _seed_document(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    provider: InMemoryVectorProvider,
    *,
    document_id: str,
    with_vectors: bool,
) -> None:
    with db.session() as session:
        session.add(
            Repository(
                id="repo-del",
                tenant_id=_TENANT,
                name="del-repo",
                source_type="local_fs",
                uri="D:/del",
            )
        )
        session.add(
            Document(
                id=document_id,
                repository_id="repo-del",
                tenant_id=_TENANT,
                source_path=f"{document_id}.md",
                content_hash="h1",
                classification_clearance="internal",
                version=1,
            )
        )
        session.add(
            Workflow(
                document_id=document_id,
                tenant_id=_TENANT,
                workflow_type="ingest",
            )
        )
        session.add(
            ProcessingState(
                document_id=document_id,
                tenant_id=_TENANT,
                stage="embed",
            )
        )
        if with_vectors:
            session.add(
                Asset(
                    document_id=document_id,
                    tenant_id=_TENANT,
                    asset_type=AssetType.VECTOR,
                    version=1,
                    storage_uri=f"asset://{_TENANT}/{document_id}/vectors?version=1",
                    content_hash="vector-content",
                )
            )

    if not with_vectors:
        return

    published = PublishedVectorSet(
        document_id=document_id,
        collection=_COLLECTION,
        provider="local",
        model_name="model",
        distance_metric="cosine",
        dimension=4,
        vector_count=1,
        source_embedding_version=1,
        records=[
            VectorRecord(
                vector_id=f"{_COLLECTION}::chk-1::e1",
                chunk_id="chk-1",
                chunk_content_hash="c1",
                state=SyncState.PUBLISHED,
            ),
        ],
    )
    provider.ensure_collection(
        CollectionSpec(name=_COLLECTION, dimension=4, distance_metric="cosine")
    )
    provider.upsert(
        _COLLECTION,
        [
            VectorPoint(
                vector_id=f"{_COLLECTION}::chk-1::e1",
                values=[0.1, 0.2, 0.3, 0.4],
                metadata=VectorMetadata(
                    document_id=document_id,
                    chunk_id="chk-1",
                    tenant_id=_TENANT,
                    classification_clearance="internal",
                    distance_metric="cosine",
                    collection=_COLLECTION,
                    embedding_model="model",
                    embedding_version=1,
                    dimension=4,
                ),
            )
        ],
    )
    storage.put(
        f"{_TENANT}/{document_id}/vectors", published.canonical_json(), version=1
    )


def _service(
    db: ControlPlaneDatabase, storage: AssetStorage, provider: InMemoryVectorProvider
) -> DocumentDeletionService:
    registry = VectorProviderRegistry([provider])
    return DocumentDeletionService(db, VectorCleanupService(db, storage, registry))


def test_delete_document_purges_vectors_and_cascades_rows(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    _seed_document(
        control_plane_db, storage, provider, document_id="doc-1", with_vectors=True
    )

    result = _service(control_plane_db, storage, provider).delete_document(
        "doc-1", _TENANT
    )

    assert result.row_deleted is True
    assert result.vectors_deleted == 1
    assert result.vector_cleanup_error is None
    assert provider.count(_COLLECTION) == 0
    with control_plane_db.session() as session:
        assert session.get(Document, "doc-1") is None
        assert session.query(Asset).filter_by(document_id="doc-1").count() == 0
        assert session.query(Workflow).filter_by(document_id="doc-1").count() == 0
        assert (
            session.query(ProcessingState).filter_by(document_id="doc-1").count() == 0
        )


def test_delete_document_without_vectors_still_removes_row(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    _seed_document(
        control_plane_db, storage, provider, document_id="doc-2", with_vectors=False
    )

    result = _service(control_plane_db, storage, provider).delete_document(
        "doc-2", _TENANT
    )

    assert result.row_deleted is True
    assert result.vectors_deleted == 0
    with control_plane_db.session() as session:
        assert session.get(Document, "doc-2") is None


def test_delete_document_unknown_id_reports_not_deleted(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()

    result = _service(control_plane_db, storage, provider).delete_document(
        "missing", _TENANT
    )

    assert result.row_deleted is False


def test_delete_purges_orphan_jobs_even_when_document_row_is_gone(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    from domain.control_plane import IngestionJob, JobKind
    from domain.jobs import JobQueueStore, SourceStore

    # Simulate the orphan case: an ingest job (and staged source) exist for a
    # document whose row was already removed by a prior/partial delete.
    JobQueueStore(control_plane_db).enqueue(
        tenant_id=_TENANT, document_id="ghost", kind=JobKind.INGEST, content_hash="h"
    )
    SourceStore(control_plane_db).store(_TENANT, "ghost", b"# bytes")

    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    result = _service(control_plane_db, storage, provider).delete_document(
        "ghost", _TENANT
    )

    # No document row to remove, but the orphaned job and source are gone so the
    # worker never dead-letters them and no manual purge is needed.
    assert result.row_deleted is False
    with control_plane_db.session() as session:
        assert (
            session.query(IngestionJob)
            .filter_by(document_id="ghost", kind=JobKind.INGEST)
            .count()
            == 0
        )
    assert SourceStore(control_plane_db).load(_TENANT, "ghost") is None


def test_delete_document_wrong_tenant_is_isolated(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    _seed_document(
        control_plane_db, storage, provider, document_id="doc-3", with_vectors=False
    )

    result = _service(control_plane_db, storage, provider).delete_document(
        "doc-3", "other-tenant"
    )

    assert result.row_deleted is False
    with control_plane_db.session() as session:
        assert session.get(Document, "doc-3") is not None


def test_delete_document_force_survives_missing_vector_payload(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    # Register a VECTOR asset row but omit the storage payload so cleanup fails.
    _seed_document(
        control_plane_db, storage, provider, document_id="doc-4", with_vectors=False
    )
    with control_plane_db.session() as session:
        session.add(
            Asset(
                document_id="doc-4",
                tenant_id=_TENANT,
                asset_type=AssetType.VECTOR,
                version=1,
                storage_uri=f"asset://{_TENANT}/doc-4/vectors?version=1",
                content_hash="missing-payload",
            )
        )

    result = _service(control_plane_db, storage, provider).delete_document(
        "doc-4", _TENANT, force=True
    )

    assert result.row_deleted is True
    assert result.vector_cleanup_error is not None
    with control_plane_db.session() as session:
        assert session.get(Document, "doc-4") is None


def _seed_orphan_vector_without_manifest(
    control_plane_db: ControlPlaneDatabase,
    provider: InMemoryVectorProvider,
    *,
    document_id: str,
) -> None:
    """Seed a document with a live vector point but no stored manifest payload."""
    with control_plane_db.session() as session:
        session.add(
            Repository(
                id="repo-del",
                tenant_id=_TENANT,
                name="del-repo",
                source_type="local_fs",
                uri="D:/del",
            )
        )
        session.add(
            Document(
                id=document_id,
                repository_id="repo-del",
                tenant_id=_TENANT,
                source_path=f"{document_id}.md",
                content_hash="h1",
                classification_clearance="internal",
                version=1,
            )
        )
        session.add(
            Asset(
                document_id=document_id,
                tenant_id=_TENANT,
                asset_type=AssetType.VECTOR,
                version=1,
                storage_uri=f"asset://{_TENANT}/{document_id}/vectors?version=1",
                content_hash="manifest-gone",
            )
        )
    provider.ensure_collection(
        CollectionSpec(name=_COLLECTION, dimension=4, distance_metric="cosine")
    )
    provider.upsert(
        _COLLECTION,
        [
            VectorPoint(
                vector_id=f"{_COLLECTION}::CHK-1::e1",
                values=[0.1, 0.2, 0.3, 0.4],
                metadata=VectorMetadata(
                    document_id=document_id,
                    chunk_id="CHK-1",
                    tenant_id=_TENANT,
                    classification_clearance="internal",
                    distance_metric="cosine",
                    collection=_COLLECTION,
                    embedding_model="model",
                    embedding_version=1,
                    dimension=4,
                ),
            )
        ],
    )


def test_delete_document_filter_fallback_reclaims_orphaned_vectors(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    _seed_orphan_vector_without_manifest(control_plane_db, provider, document_id="doc-fb")

    registry = VectorProviderRegistry([provider])
    cleanup = VectorCleanupService(
        control_plane_db,
        storage,
        registry,
        fallback_provider="local",
        fallback_collection=_COLLECTION,
    )
    result = DocumentDeletionService(control_plane_db, cleanup).delete_document(
        "doc-fb", _TENANT
    )

    assert result.row_deleted is True
    assert result.vectors_deleted == 1
    assert result.vector_cleanup_error is None
    assert provider.count(_COLLECTION) == 0
    with control_plane_db.session() as session:
        assert session.get(Document, "doc-fb") is None


def test_delete_document_also_removes_pending_jobs_and_source(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    from domain.control_plane import IngestionJob, IngestionSource, JobKind
    from domain.jobs import JobQueueStore, SourceStore

    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    _seed_document(
        control_plane_db, storage, provider, document_id="doc-cascade", with_vectors=False
    )
    JobQueueStore(control_plane_db).enqueue(
        tenant_id=_TENANT, document_id="doc-cascade", kind=JobKind.INGEST, content_hash="h"
    )
    SourceStore(control_plane_db).store(_TENANT, "doc-cascade", b"# source")

    _service(control_plane_db, storage, provider).delete_document(
        "doc-cascade", _TENANT
    )

    with control_plane_db.session() as session:
        assert (
            session.query(IngestionJob).filter_by(document_id="doc-cascade").count() == 0
        )
        assert (
            session.query(IngestionSource)
            .filter_by(document_id="doc-cascade")
            .count()
            == 0
        )


def test_provider_delete_by_document_is_tenant_scoped() -> None:
    provider = InMemoryVectorProvider()
    provider.ensure_collection(
        CollectionSpec(name=_COLLECTION, dimension=4, distance_metric="cosine")
    )

    def _point(vector_id: str, document_id: str, tenant_id: str) -> VectorPoint:
        return VectorPoint(
            vector_id=vector_id,
            values=[0.1, 0.2, 0.3, 0.4],
            metadata=VectorMetadata(
                document_id=document_id,
                chunk_id="c",
                tenant_id=tenant_id,
                classification_clearance="internal",
                distance_metric="cosine",
                collection=_COLLECTION,
                embedding_model="model",
                embedding_version=1,
                dimension=4,
            ),
        )

    provider.upsert(
        _COLLECTION,
        [
            _point("v1", "doc-x", _TENANT),
            _point("v2", "doc-x", "other-tenant"),
            _point("v3", "doc-y", _TENANT),
        ],
    )

    removed = provider.delete_by_document(_COLLECTION, _TENANT, "doc-x")

    assert removed == 1
    assert provider.count(_COLLECTION) == 2
    assert provider.delete_by_document("missing-collection", _TENANT, "doc-x") == 0

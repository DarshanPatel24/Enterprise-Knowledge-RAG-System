from __future__ import annotations

from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    Repository,
)
from domain.publishing import (
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
from domain.storage import InMemoryAssetStorage


def test_vector_cleanup_removes_vectors_for_deleted_document(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    storage = InMemoryAssetStorage()
    provider = InMemoryVectorProvider()
    registry = VectorProviderRegistry([provider])

    document_id = "doc-cleanup"
    tenant_id = "tenant-cleanup"

    with control_plane_db.session() as session:
        session.add(
            Repository(
                id="repo-cleanup",
                tenant_id=tenant_id,
                name="cleanup-repo",
                source_type="local_fs",
                uri="D:/cleanup",
            )
        )
        document = Document(
            id=document_id,
            repository_id="repo-cleanup",
            tenant_id=tenant_id,
            source_path="deleted.md",
            content_hash="h1",
            classification_clearance="internal",
            version=1,
        )
        session.add(document)
        session.add(
            Asset(
                document_id=document_id,
                tenant_id=tenant_id,
                asset_type=AssetType.VECTOR,
                version=1,
                storage_uri=f"asset://{tenant_id}/{document_id}/vectors?version=1",
                content_hash="vector-content",
            )
        )

    published = PublishedVectorSet(
        document_id=document_id,
        collection="enterprise_documents",
        provider="local",
        model_name="model",
        distance_metric="cosine",
        dimension=4,
        vector_count=2,
        source_embedding_version=1,
        records=[
            VectorRecord(
                vector_id="enterprise_documents::chk-1::e1",
                chunk_id="chk-1",
                chunk_content_hash="c1",
                state=SyncState.PUBLISHED,
            ),
            VectorRecord(
                vector_id="enterprise_documents::chk-2::e1",
                chunk_id="chk-2",
                chunk_content_hash="c2",
                state=SyncState.PUBLISHED,
            ),
        ],
    )

    provider.ensure_collection(
        CollectionSpec(name="enterprise_documents", dimension=4, distance_metric="cosine")
    )

    for vector_id in [record.vector_id for record in published.records]:
        provider.upsert(
            "enterprise_documents",
            [
                VectorPoint(
                    vector_id=vector_id,
                    values=[0.1, 0.2, 0.3, 0.4],
                    metadata=VectorMetadata(
                        document_id=document_id,
                        chunk_id="chk",
                        tenant_id=tenant_id,
                        classification_clearance="internal",
                        distance_metric="cosine",
                        collection="enterprise_documents",
                        embedding_model="model",
                        embedding_version=1,
                        dimension=4,
                    ),
                )
            ],
        )

    storage.put(
        f"{tenant_id}/{document_id}/vectors",
        published.canonical_json(),
        version=1,
    )

    service = VectorCleanupService(control_plane_db, storage, registry)
    result = service.purge_document_vectors(document_id, tenant_id)

    assert result is not None
    assert result.deleted_count == 2
    assert provider.count("enterprise_documents") == 0

"""Read-back loaders for persisted ingestion assets (handbook Chapter 20).

Validators and the EKRE handoff builder inspect the immutable assets produced by
the pipeline. These helpers resolve the latest asset of a given type from the
Control Plane and deserialize its payload from object storage, mirroring the keys
the engines write. Missing assets return ``None`` so validators can report them
rather than raise.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.chunking.models import ChunkDocument
from domain.control_plane import Asset, AssetType, ControlPlaneDatabase, Lineage
from domain.embedding.models import EmbeddingDocument
from domain.publishing.models import PublishedVectorSet
from domain.storage import AssetStorage

_ASSET_KEY_SUFFIX: dict[AssetType, str] = {
    AssetType.CHUNKS: "chunks",
    AssetType.EMBEDDING: "embedding",
    AssetType.VECTOR: "vectors",
}


@dataclass(frozen=True)
class PipelineAssets:
    """The read-back asset documents for a completed document ingestion."""

    chunks: ChunkDocument | None
    embedding: EmbeddingDocument | None
    vectors: PublishedVectorSet | None


def _latest_version(
    db: ControlPlaneDatabase, document_id: str, asset_type: AssetType
) -> int | None:
    """Return the highest asset version of ``asset_type`` for a document."""
    with db.session() as session:
        asset = (
            session.query(Asset)
            .filter(
                Asset.document_id == document_id,
                Asset.asset_type == asset_type,
            )
            .order_by(Asset.version.desc())
            .first()
        )
        return None if asset is None else asset.version


def _load_payload(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    *,
    document_id: str,
    tenant_id: str,
    asset_type: AssetType,
) -> str | None:
    """Return the decoded payload of the latest asset, or ``None`` if absent."""
    version = _latest_version(db, document_id, asset_type)
    if version is None:
        return None
    key = f"{tenant_id}/{document_id}/{_ASSET_KEY_SUFFIX[asset_type]}"
    try:
        return storage.get(key, version=version).decode("utf-8")
    except (KeyError, OSError):
        return None


def load_chunks(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    *,
    document_id: str,
    tenant_id: str,
) -> ChunkDocument | None:
    """Load and deserialize the latest CHUNKS asset."""
    payload = _load_payload(
        db, storage, document_id=document_id, tenant_id=tenant_id,
        asset_type=AssetType.CHUNKS,
    )
    return None if payload is None else ChunkDocument.model_validate_json(payload)


def load_embedding(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    *,
    document_id: str,
    tenant_id: str,
) -> EmbeddingDocument | None:
    """Load and deserialize the latest EMBEDDING asset."""
    payload = _load_payload(
        db, storage, document_id=document_id, tenant_id=tenant_id,
        asset_type=AssetType.EMBEDDING,
    )
    return None if payload is None else EmbeddingDocument.model_validate_json(payload)


def load_vectors(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    *,
    document_id: str,
    tenant_id: str,
) -> PublishedVectorSet | None:
    """Load and deserialize the latest VECTOR asset."""
    payload = _load_payload(
        db, storage, document_id=document_id, tenant_id=tenant_id,
        asset_type=AssetType.VECTOR,
    )
    return None if payload is None else PublishedVectorSet.model_validate_json(payload)


def load_pipeline_assets(
    db: ControlPlaneDatabase,
    storage: AssetStorage,
    *,
    document_id: str,
    tenant_id: str,
) -> PipelineAssets:
    """Load all read-back asset documents for a document in one call."""
    return PipelineAssets(
        chunks=load_chunks(
            db, storage, document_id=document_id, tenant_id=tenant_id
        ),
        embedding=load_embedding(
            db, storage, document_id=document_id, tenant_id=tenant_id
        ),
        vectors=load_vectors(
            db, storage, document_id=document_id, tenant_id=tenant_id
        ),
    )


def present_asset_types(
    db: ControlPlaneDatabase, document_id: str
) -> set[AssetType]:
    """Return the set of asset types persisted for a document."""
    with db.session() as session:
        return {
            asset.asset_type
            for asset in session.query(Asset).filter(
                Asset.document_id == document_id
            )
        }


def lineage_relations(db: ControlPlaneDatabase, document_id: str) -> set[str]:
    """Return the set of lineage relation labels recorded for a document."""
    with db.session() as session:
        asset_ids = [
            asset.id
            for asset in session.query(Asset).filter(
                Asset.document_id == document_id
            )
        ]
        if not asset_ids:
            return set()
        return {
            row.relation
            for row in session.query(Lineage).filter(
                Lineage.asset_id.in_(asset_ids)
            )
        }

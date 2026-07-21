"""Vector publishing engine: publishes validated embeddings to the vector DB.

Reads a document's embedding asset, resolves the target collection and enforces
its schema, maps complete governance metadata, publishes vectors idempotently in
batches with retry, verifies durable storage, and records a versioned managed
VECTOR asset with lineage back to the embedding asset (handbook 11.6, ADR-025 to
ADR-028).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from domain.chunking import ChunkDocument
from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    Lineage,
)
from domain.control_plane.progress import NullProgressReporter, ProgressReporter
from domain.embedding import EmbeddingDocument, RateLimiter, batched, run_with_retry
from domain.publishing.collections import CollectionResolver, CollectionSpec
from domain.publishing.errors import PublishError, PublishErrorType
from domain.publishing.events import PublishEvent, PublishEventType
from domain.publishing.identity import build_vector_id
from domain.publishing.metadata import derive_source_group, missing_required_fields
from domain.publishing.models import (
    PublishedVectorSet,
    SyncState,
    VectorMetadata,
    VectorPoint,
    VectorRecord,
)
from domain.publishing.policy import PublishingPolicy
from domain.publishing.providers import (
    VectorProvider,
    VectorProviderError,
    VectorProviderRegistry,
    default_provider_registry,
)
from domain.publishing.verification import PublishVerifier
from domain.storage import AssetStorage, compute_content_hash


@dataclass(frozen=True)
class PublishResult:
    """Outcome of publishing a single document's vectors."""

    document_id: str
    asset_id: str
    version: int
    storage_uri: str
    content_hash: str
    created: bool
    collection: str
    provider: str
    dimension: int
    vector_count: int
    verified_count: int
    batch_count: int
    published_vector_set: PublishedVectorSet
    publish_ms: float
    events: list[PublishEvent] = field(default_factory=list)


@dataclass(frozen=True)
class _AssetRef:
    asset_id: str
    version: int
    content: str


@dataclass(frozen=True)
class _ChunkFacts:
    section_id: str | None
    section_title: str | None
    language: str
    content: str


class VectorPublishingEngine:
    """Publishes and verifies versioned vector assets in the vector database."""

    def __init__(
        self,
        db: ControlPlaneDatabase,
        storage: AssetStorage,
        policy: PublishingPolicy,
        *,
        provider_registry: VectorProviderRegistry | None = None,
        rate_limiter: RateLimiter | None = None,
        progress_reporter: ProgressReporter | None = None,
    ) -> None:
        self._db = db
        self._storage = storage
        self._policy = policy
        self._providers = provider_registry or default_provider_registry()
        self._collections = CollectionResolver(policy)
        self._rate_limiter = rate_limiter or RateLimiter(policy.max_vectors_per_minute)
        self._progress = progress_reporter or NullProgressReporter()

    def publish(self, document_id: str, tenant_id: str) -> PublishResult:
        """Publish a document's latest embedding set as a versioned vector asset."""
        events = [self._event(PublishEventType.PUBLISH_STARTED, document_id, tenant_id)]
        try:
            document = self._load_document(document_id, tenant_id)
            embedding_ref = self._load_embedding(document_id, tenant_id)
            embedding_document = EmbeddingDocument.model_validate_json(embedding_ref.content)
            if not embedding_document.records:
                raise PublishError(
                    PublishErrorType.EMPTY_RESULT,
                    f"embedding set for document {document_id!r} is empty",
                )

            provider = self._resolve_provider()
            spec = self._collections.resolve(document, embedding_document)
            self._ensure_collection(provider, spec)
            events.append(
                self._event(
                    PublishEventType.COLLECTION_READY,
                    document_id,
                    tenant_id,
                    collection=spec.name,
                    detail=f"dim={spec.dimension} metric={spec.distance_metric}",
                )
            )

            chunk_facts = self._load_chunk_facts(document_id, tenant_id)
            points = self._build_points(
                document, embedding_document, embedding_ref.version, spec, chunk_facts
            )
            published_set = self._build_published_set(
                document_id, embedding_document, embedding_ref.version, spec, points
            )
            payload = published_set.canonical_json()
            content_hash = compute_content_hash(payload)

            existing = self._existing_asset(document_id, content_hash)
            if existing is not None:
                events.append(
                    self._event(
                        PublishEventType.PUBLISH_SKIPPED,
                        document_id,
                        tenant_id,
                        collection=spec.name,
                        asset_id=existing[0],
                        version=existing[1],
                        detail="identical vector set already published; reusing asset",
                    )
                )
                return self._result(
                    document_id,
                    existing[0],
                    existing[1],
                    spec,
                    f"asset://{tenant_id}/{document_id}/vectors?version={existing[1]}",
                    content_hash,
                    False,
                    published_set,
                    len(points),
                    0,
                    0,
                    0.0,
                    events,
                )

            batch_count, verified_count, publish_ms = self._publish_points(
                provider, spec.name, points, document_id, tenant_id
            )
            events.append(
                self._event(
                    PublishEventType.VECTORS_PUBLISHED,
                    document_id,
                    tenant_id,
                    collection=spec.name,
                    detail=f"{len(points)} vectors in {batch_count} batches",
                )
            )
            if self._policy.verify_after_publish:
                events.append(
                    self._event(
                        PublishEventType.VECTORS_VERIFIED,
                        document_id,
                        tenant_id,
                        collection=spec.name,
                        detail=f"{verified_count} vectors verified",
                    )
                )

            return self._persist(
                document_id,
                tenant_id,
                embedding_ref,
                spec,
                content_hash,
                payload,
                published_set,
                len(points),
                verified_count,
                batch_count,
                publish_ms,
                events,
            )
        except PublishError as exc:
            events.append(
                self._event(
                    PublishEventType.PUBLISH_FAILED,
                    document_id,
                    tenant_id,
                    detail=f"{exc.error_type.value}: {exc}",
                )
            )
            raise

    def _resolve_provider(self) -> VectorProvider:
        try:
            return self._providers.get(self._policy.provider)
        except VectorProviderError as exc:
            raise PublishError(PublishErrorType.UNSUPPORTED_PROVIDER, str(exc)) from exc

    def _ensure_collection(self, provider: VectorProvider, spec: CollectionSpec) -> None:
        try:
            if self._policy.create_missing_collections:
                provider.ensure_collection(spec)
            else:
                provider.count(spec.name)
        except VectorProviderError as exc:
            raise PublishError(PublishErrorType.COLLECTION_UNAVAILABLE, str(exc)) from exc

    def _build_points(
        self,
        document: Document,
        embedding_document: EmbeddingDocument,
        embedding_version: int,
        spec: CollectionSpec,
        chunk_facts: dict[str, _ChunkFacts],
    ) -> list[VectorPoint]:
        source_group = (
            derive_source_group(
                document.source_path,
                depth=self._policy.source_group_depth,
                default=self._policy.default_source_group,
            )
            if self._policy.derive_source_group_from_path
            else self._policy.default_source_group
        )
        points: list[VectorPoint] = []
        for record in embedding_document.records:
            facts = chunk_facts.get(record.chunk_id)
            metadata = VectorMetadata(
                document_id=document.id,
                chunk_id=record.chunk_id,
                tenant_id=document.tenant_id,
                classification_clearance=document.classification_clearance,
                distance_metric=embedding_document.distance_metric,
                collection=spec.name,
                embedding_model=embedding_document.model_name,
                embedding_version=embedding_version,
                dimension=embedding_document.dimension,
                repository_id=document.repository_id,
                source_path=document.source_path,
                source_group=source_group,
                section_id=facts.section_id if facts else None,
                section_title=facts.section_title if facts else None,
                language=facts.language if facts else "",
                content=facts.content if facts else "",
            )
            missing = missing_required_fields(metadata)
            if missing:
                raise PublishError(
                    PublishErrorType.REQUIRED_FIELD_MISSING,
                    f"vector for chunk {record.chunk_id!r} is missing mandatory "
                    f"metadata: {', '.join(missing)}",
                )
            points.append(
                VectorPoint(
                    vector_id=build_vector_id(
                        spec.name, document.id, record.chunk_id, embedding_version
                    ),
                    values=record.values,
                    metadata=metadata,
                )
            )
        return points

    def _build_published_set(
        self,
        document_id: str,
        embedding_document: EmbeddingDocument,
        embedding_version: int,
        spec: CollectionSpec,
        points: list[VectorPoint],
    ) -> PublishedVectorSet:
        final_state = (
            SyncState.VERIFIED if self._policy.verify_after_publish else SyncState.PUBLISHED
        )
        record_hashes = {
            record.chunk_id: record.chunk_content_hash
            for record in embedding_document.records
        }
        records = [
            VectorRecord(
                vector_id=point.vector_id,
                chunk_id=point.metadata.chunk_id,
                chunk_content_hash=record_hashes.get(point.metadata.chunk_id, ""),
                state=final_state,
            )
            for point in points
        ]
        return PublishedVectorSet(
            document_id=document_id,
            collection=spec.name,
            provider=self._policy.provider,
            model_name=embedding_document.model_name,
            distance_metric=embedding_document.distance_metric,
            dimension=embedding_document.dimension,
            vector_count=len(points),
            source_embedding_version=embedding_version,
            records=records,
        )

    def _publish_points(
        self,
        provider: VectorProvider,
        collection: str,
        points: list[VectorPoint],
        document_id: str,
        tenant_id: str,
    ) -> tuple[int, int, float]:
        batch_count = 0
        published = 0
        total_points = len(points)
        started = time.perf_counter()
        # Publish 0/total up front so observers see the stage begin immediately.
        self._progress.report(
            document_id=document_id, tenant_id=tenant_id, stage="vector",
            processed=0, total=total_points,
        )
        for batch in batched(points, self._policy.batch_size):
            batch_count += 1
            self._rate_limiter.acquire(len(batch))
            self._upsert_batch(provider, collection, batch)
            published += len(batch)
            self._progress.report(
                document_id=document_id, tenant_id=tenant_id, stage="vector",
                processed=published, total=total_points,
            )

        verified_count = 0
        if self._policy.verify_after_publish:
            report = PublishVerifier(provider).verify(collection, points)
            if not report.verified:
                raise PublishError(
                    PublishErrorType.VERIFICATION_FAILURE,
                    "; ".join(report.messages),
                )
            verified_count = report.verified_count

        publish_ms = round((time.perf_counter() - started) * 1000.0, 3)
        return batch_count, verified_count, publish_ms

    def _upsert_batch(
        self, provider: VectorProvider, collection: str, batch: list[VectorPoint]
    ) -> None:
        def _call() -> None:
            provider.upsert(collection, batch)

        try:
            run_with_retry(
                _call,
                max_retries=self._policy.max_retries,
                retryable=VectorProviderError,
            )
        except VectorProviderError as exc:
            raise PublishError(PublishErrorType.PROVIDER_FAILURE, str(exc)) from exc

    def _persist(
        self,
        document_id: str,
        tenant_id: str,
        embedding_ref: _AssetRef,
        spec: CollectionSpec,
        content_hash: str,
        payload: bytes,
        published_set: PublishedVectorSet,
        vector_count: int,
        verified_count: int,
        batch_count: int,
        publish_ms: float,
        events: list[PublishEvent],
    ) -> PublishResult:
        key = f"{tenant_id}/{document_id}/vectors"
        try:
            stored = self._storage.put_next(key, payload)
        except OSError as exc:  # pragma: no cover - local storage rarely fails
            raise PublishError(PublishErrorType.STORAGE_FAILURE, str(exc)) from exc
        storage_uri = f"asset://{key}?version={stored.version}"
        asset_id = self._record_asset(
            document_id,
            tenant_id,
            stored.version,
            storage_uri,
            content_hash,
            embedding_ref.asset_id,
            metrics={
                "vector_count": vector_count,
                "verified_count": verified_count,
                "batch_count": batch_count,
            },
        )
        events.append(
            self._event(
                PublishEventType.ASSET_STORED,
                document_id,
                tenant_id,
                collection=spec.name,
                asset_id=asset_id,
                version=stored.version,
            )
        )
        return self._result(
            document_id,
            asset_id,
            stored.version,
            spec,
            storage_uri,
            content_hash,
            True,
            published_set,
            vector_count,
            verified_count,
            batch_count,
            publish_ms,
            events,
        )

    def _result(
        self,
        document_id: str,
        asset_id: str,
        version: int,
        spec: CollectionSpec,
        storage_uri: str,
        content_hash: str,
        created: bool,
        published_set: PublishedVectorSet,
        vector_count: int,
        verified_count: int,
        batch_count: int,
        publish_ms: float,
        events: list[PublishEvent],
    ) -> PublishResult:
        return PublishResult(
            document_id=document_id,
            asset_id=asset_id,
            version=version,
            storage_uri=storage_uri,
            content_hash=content_hash,
            created=created,
            collection=spec.name,
            provider=self._policy.provider,
            dimension=spec.dimension,
            vector_count=vector_count,
            verified_count=verified_count,
            batch_count=batch_count,
            published_vector_set=published_set,
            publish_ms=publish_ms,
            events=events,
        )

    def _load_document(self, document_id: str, tenant_id: str) -> Document:
        with self._db.session() as session:
            document = session.get(Document, document_id)
            if document is None or document.tenant_id != tenant_id:
                raise PublishError(
                    PublishErrorType.NOT_FOUND,
                    f"document {document_id!r} not found for tenant {tenant_id!r}",
                )
            session.expunge(document)
            return document

    def _load_embedding(self, document_id: str, tenant_id: str) -> _AssetRef:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(
                    Asset.document_id == document_id,
                    Asset.asset_type == AssetType.EMBEDDING,
                )
                .order_by(Asset.version.desc())
                .first()
            )
            if asset is None:
                raise PublishError(
                    PublishErrorType.MISSING_EMBEDDING,
                    f"no embedding asset for document {document_id!r}; embed it first",
                )
            asset_id = asset.id
            version = asset.version
        key = f"{tenant_id}/{document_id}/embedding"
        try:
            content = self._storage.get(key, version=version).decode("utf-8")
        except (KeyError, OSError) as exc:
            raise PublishError(
                PublishErrorType.MISSING_EMBEDDING,
                f"embedding payload unavailable for document {document_id!r}",
            ) from exc
        return _AssetRef(asset_id=asset_id, version=version, content=content)

    def _load_chunk_facts(
        self, document_id: str, tenant_id: str
    ) -> dict[str, _ChunkFacts]:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(
                    Asset.document_id == document_id,
                    Asset.asset_type == AssetType.CHUNKS,
                )
                .order_by(Asset.version.desc())
                .first()
            )
            version = asset.version if asset is not None else None
        if version is None:
            return {}
        key = f"{tenant_id}/{document_id}/chunks"
        try:
            content = self._storage.get(key, version=version).decode("utf-8")
        except (KeyError, OSError):
            return {}
        chunk_document = ChunkDocument.model_validate_json(content)
        return {
            chunk.metadata.chunk_id: _ChunkFacts(
                section_id=chunk.metadata.section_id,
                section_title=chunk.metadata.section_title,
                language=chunk.metadata.language,
                content=chunk.content,
            )
            for chunk in chunk_document.chunks
        }

    def _existing_asset(self, document_id: str, content_hash: str) -> tuple[str, int] | None:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(
                    Asset.document_id == document_id,
                    Asset.asset_type == AssetType.VECTOR,
                )
                .order_by(Asset.version.desc())
                .first()
            )
            if asset is None or asset.content_hash != content_hash:
                return None
            return asset.id, asset.version

    def _record_asset(
        self,
        document_id: str,
        tenant_id: str,
        version: int,
        storage_uri: str,
        content_hash: str,
        parent_asset_id: str,
        metrics: dict[str, int | float | str] | None = None,
    ) -> str:
        with self._db.session() as session:
            asset = Asset(
                document_id=document_id,
                tenant_id=tenant_id,
                asset_type=AssetType.VECTOR,
                version=version,
                storage_uri=storage_uri,
                content_hash=content_hash,
                stage_metrics=json.dumps(metrics) if metrics is not None else None,
            )
            session.add(asset)
            session.flush()
            session.add(
                Lineage(
                    asset_id=asset.id,
                    parent_asset_id=parent_asset_id,
                    relation="published_from_embedding",
                )
            )
            return asset.id

    def _event(
        self,
        event_type: PublishEventType,
        document_id: str,
        tenant_id: str,
        *,
        collection: str = "",
        asset_id: str | None = None,
        version: int | None = None,
        detail: str = "",
    ) -> PublishEvent:
        return PublishEvent(
            event_type=event_type,
            document_id=document_id,
            tenant_id=tenant_id,
            collection=collection,
            asset_id=asset_id,
            version=version,
            detail=detail,
        )

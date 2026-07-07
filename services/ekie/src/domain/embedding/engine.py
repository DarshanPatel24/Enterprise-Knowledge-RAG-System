"""Embedding engine: converts validated chunks into versioned embedding assets.

Reads a document's chunk set, selects an approved model via policy, generates
vectors through a provider-abstracted plugin with batching and retry, validates
each vector, and persists a deterministic, versioned embedding asset with
lineage back to the chunk asset (handbook 10.8, ADR-022/ADR-023).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from domain.chunking import Chunk, ChunkDocument
from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    Lineage,
)
from domain.control_plane.progress import NullProgressReporter, ProgressReporter
from domain.embedding.errors import EmbeddingError, EmbeddingErrorType
from domain.embedding.events import EmbeddingEvent, EmbeddingEventType
from domain.embedding.model_registry import EmbeddingModelRegistry, default_model_registry
from domain.embedding.models import (
    EmbeddingDocument,
    EmbeddingModelSpec,
    EmbeddingRecord,
    EmbeddingStatus,
)
from domain.embedding.policy import EmbeddingPolicy
from domain.embedding.providers import (
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderRegistry,
    default_provider_registry,
)
from domain.embedding.rate_limit import RateLimiter
from domain.embedding.retry import run_with_retry
from domain.embedding.selection import ModelSelectionError, ModelSelector
from domain.embedding.tokens import batched, estimate_cost, estimate_tokens
from domain.embedding.validation import EmbeddingValidator
from domain.storage import AssetStorage, compute_content_hash


@dataclass(frozen=True)
class EmbeddingResult:
    """Outcome of embedding a single document."""

    document_id: str
    asset_id: str
    version: int
    storage_uri: str
    content_hash: str
    created: bool
    model_name: str
    provider: str
    dimension: int
    embedding_document: EmbeddingDocument
    batch_count: int
    total_tokens: int
    cost_estimate: float
    generation_ms: float
    events: list[EmbeddingEvent] = field(default_factory=list)


@dataclass(frozen=True)
class _AssetRef:
    asset_id: str
    version: int
    content: str


class EmbeddingEngine:
    """Generates and persists versioned, validated embedding assets."""

    def __init__(
        self,
        db: ControlPlaneDatabase,
        storage: AssetStorage,
        policy: EmbeddingPolicy,
        *,
        provider_registry: EmbeddingProviderRegistry | None = None,
        model_registry: EmbeddingModelRegistry | None = None,
        rate_limiter: RateLimiter | None = None,
        progress_reporter: ProgressReporter | None = None,
    ) -> None:
        self._db = db
        self._storage = storage
        self._policy = policy
        self._providers = provider_registry or default_provider_registry()
        self._models = model_registry or default_model_registry(policy)
        self._selector = ModelSelector(self._models)
        self._rate_limiter = rate_limiter or RateLimiter(policy.max_requests_per_minute)
        self._progress = progress_reporter or NullProgressReporter()

    def embed(
        self,
        document_id: str,
        tenant_id: str,
        *,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> EmbeddingResult:
        """Embed a document's latest chunk set into a versioned asset."""
        events = [self._event(EmbeddingEventType.EMBEDDING_STARTED, document_id, tenant_id)]
        
        policy = self._policy
        selector = self._selector
        if provider_override or model_override:
            updates: dict[str, object] = {}
            if provider_override:
                updates["provider"] = provider_override
            if model_override:
                updates["default_model"] = model_override
            policy = policy.model_copy(update=updates)
            
            # Generate a temporary registry for this execution so the overridden 
            # model is discoverable by the selector.
            selector = ModelSelector(default_model_registry(policy))

        try:
            document = self._load_document(document_id, tenant_id)
            chunks_ref = self._load_chunks(document_id, tenant_id)
            chunk_document = ChunkDocument.model_validate_json(chunks_ref.content)
            if not chunk_document.chunks:
                raise EmbeddingError(
                    EmbeddingErrorType.EMPTY_RESULT,
                    f"chunk set for document {document_id!r} is empty",
                )
            model = self._select_model(document, chunk_document, policy, selector)
            events.append(
                self._event(
                    EmbeddingEventType.MODEL_SELECTED,
                    document_id,
                    tenant_id,
                    detail=f"{model.name} ({model.provider}, dim={model.dimensions})",
                )
            )
            embedding_document, batch_count, generation_ms = self._generate(
                document_id, tenant_id, chunk_document, model
            )
            events.append(
                self._event(
                    EmbeddingEventType.EMBEDDINGS_GENERATED,
                    document_id,
                    tenant_id,
                    detail=f"{embedding_document.embedding_count} vectors in {batch_count} batches",
                )
            )
            events.append(
                self._event(EmbeddingEventType.EMBEDDINGS_VALIDATED, document_id, tenant_id)
            )
            return self._persist(
                document_id,
                tenant_id,
                chunks_ref,
                embedding_document,
                batch_count,
                generation_ms,
                events,
            )
        except EmbeddingError as exc:
            events.append(
                self._event(
                    EmbeddingEventType.EMBEDDING_FAILED,
                    document_id,
                    tenant_id,
                    detail=f"{exc.error_type.value}: {exc}",
                )
            )
            raise

    def _select_model(
        self, 
        document: Document, 
        chunk_document: ChunkDocument, 
        policy: EmbeddingPolicy,
        selector: ModelSelector
    ) -> EmbeddingModelSpec:
        language = chunk_document.chunks[0].metadata.language
        try:
            return selector.select(
                policy,
                language=language,
                classification=document.classification_clearance,
            )
        except ModelSelectionError as exc:
            raise EmbeddingError(EmbeddingErrorType.UNSUPPORTED_MODEL, str(exc)) from exc

    def _generate(
        self,
        document_id: str,
        tenant_id: str,
        chunk_document: ChunkDocument,
        model: EmbeddingModelSpec,
    ) -> tuple[EmbeddingDocument, int, float]:
        try:
            provider = self._providers.get(model.provider)
        except EmbeddingProviderError as exc:
            raise EmbeddingError(EmbeddingErrorType.UNSUPPORTED_MODEL, str(exc)) from exc

        validator = EmbeddingValidator(model.dimensions)
        chunks = list(chunk_document.chunks)
        total_chunks = len(chunks)
        self._validate_tokens(chunks, model)

        records: list[EmbeddingRecord] = []
        batch_count = 0
        total_tokens = 0
        started = time.perf_counter()
        # Publish 0/total up front so observers see the stage begin immediately.
        self._progress.report(
            document_id=document_id, tenant_id=tenant_id, stage="embedding",
            processed=0, total=total_chunks,
        )
        for batch in batched(chunks, self._policy.batch_size):
            batch_count += 1
            self._rate_limiter.acquire(1)
            vectors = self._embed_batch(
                provider, [chunk.content for chunk in batch], model.dimensions
            )
            for chunk, vector in zip(batch, vectors, strict=True):
                self._validate_vector(validator, vector, chunk)
                tokens = estimate_tokens(chunk.content)
                total_tokens += tokens
                records.append(
                    EmbeddingRecord(
                        embedding_id=f"EMB-{len(records) + 1:06d}",
                        chunk_id=chunk.metadata.chunk_id,
                        chunk_content_hash=chunk.content_hash,
                        token_count=tokens,
                        cost_estimate=estimate_cost(tokens, self._policy.cost_per_1k_tokens),
                        status=EmbeddingStatus.READY,
                        values=vector,
                    )
                )
            self._progress.report(
                document_id=document_id, tenant_id=tenant_id, stage="embedding",
                processed=len(records), total=total_chunks,
            )
        generation_ms = round((time.perf_counter() - started) * 1000.0, 3)

        embedding_document = EmbeddingDocument(
            document_id=document_id,
            source_markdown_version=chunk_document.markdown_version,
            model_name=model.name,
            provider=model.provider,
            dimension=model.dimensions,
            distance_metric=model.distance_metric,
            embedding_count=len(records),
            total_tokens=total_tokens,
            records=records,
        )
        return embedding_document, batch_count, generation_ms

    def _validate_tokens(
        self, chunks: list[Chunk], model: EmbeddingModelSpec
    ) -> None:
        for chunk in chunks:
            tokens = estimate_tokens(chunk.content)
            if tokens > model.max_input_tokens:
                raise EmbeddingError(
                    EmbeddingErrorType.TOKEN_LIMIT_EXCEEDED,
                    f"chunk {chunk.metadata.chunk_id!r} has {tokens} tokens; "
                    f"model {model.name!r} allows {model.max_input_tokens}",
                )

    def _embed_batch(
        self, provider: EmbeddingProvider, texts: list[str], dimension: int
    ) -> list[list[float]]:
        def _call() -> list[list[float]]:
            return provider.embed(
                texts,
                dimension=dimension,
                normalize=self._policy.normalize_vectors,
            )

        try:
            return run_with_retry(
                _call,
                max_retries=self._policy.max_retries,
                retryable=EmbeddingProviderError,
            )
        except EmbeddingProviderError as exc:
            raise EmbeddingError(EmbeddingErrorType.PROVIDER_FAILURE, str(exc)) from exc

    @staticmethod
    def _validate_vector(
        validator: EmbeddingValidator, vector: list[float], chunk: Chunk
    ) -> None:
        report = validator.validate(vector)
        if not report.valid:
            raise EmbeddingError(
                EmbeddingErrorType.VALIDATION_FAILURE,
                f"chunk {chunk.metadata.chunk_id!r}: " + "; ".join(report.messages),
            )

    def _persist(
        self,
        document_id: str,
        tenant_id: str,
        chunks_ref: _AssetRef,
        embedding_document: EmbeddingDocument,
        batch_count: int,
        generation_ms: float,
        events: list[EmbeddingEvent],
    ) -> EmbeddingResult:
        payload = embedding_document.canonical_json()
        content_hash = compute_content_hash(payload)
        key = f"{tenant_id}/{document_id}/embedding"
        cost_estimate = round(
            sum(record.cost_estimate for record in embedding_document.records), 6
        )

        existing = self._existing_asset(document_id, content_hash)
        if existing is not None:
            events.append(
                self._event(
                    EmbeddingEventType.EMBEDDING_SKIPPED,
                    document_id,
                    tenant_id,
                    asset_id=existing[0],
                    version=existing[1],
                    detail="identical embedding set; reusing existing asset",
                )
            )
            return self._result(
                document_id,
                existing[0],
                existing[1],
                key,
                content_hash,
                False,
                embedding_document,
                batch_count,
                cost_estimate,
                generation_ms,
                events,
            )

        try:
            stored = self._storage.put_next(key, payload)
        except OSError as exc:  # pragma: no cover - local storage rarely fails
            raise EmbeddingError(EmbeddingErrorType.STORAGE_FAILURE, str(exc)) from exc
        storage_uri = f"asset://{key}?version={stored.version}"
        asset_id = self._record_asset(
            document_id,
            tenant_id,
            stored.version,
            storage_uri,
            content_hash,
            chunks_ref.asset_id,
            metrics={
                "embedding_count": embedding_document.embedding_count,
                "total_tokens": embedding_document.total_tokens,
                "batch_count": batch_count,
                "dimension": embedding_document.dimension,
            },
        )
        events.append(
            self._event(
                EmbeddingEventType.ASSET_STORED,
                document_id,
                tenant_id,
                asset_id=asset_id,
                version=stored.version,
            )
        )
        return self._result(
            document_id,
            asset_id,
            stored.version,
            key,
            content_hash,
            True,
            embedding_document,
            batch_count,
            cost_estimate,
            generation_ms,
            events,
        )

    def _result(
        self,
        document_id: str,
        asset_id: str,
        version: int,
        key: str,
        content_hash: str,
        created: bool,
        embedding_document: EmbeddingDocument,
        batch_count: int,
        cost_estimate: float,
        generation_ms: float,
        events: list[EmbeddingEvent],
    ) -> EmbeddingResult:
        return EmbeddingResult(
            document_id=document_id,
            asset_id=asset_id,
            version=version,
            storage_uri=f"asset://{key}?version={version}",
            content_hash=content_hash,
            created=created,
            model_name=embedding_document.model_name,
            provider=embedding_document.provider,
            dimension=embedding_document.dimension,
            embedding_document=embedding_document,
            batch_count=batch_count,
            total_tokens=embedding_document.total_tokens,
            cost_estimate=cost_estimate,
            generation_ms=generation_ms,
            events=events,
        )

    def _load_document(self, document_id: str, tenant_id: str) -> Document:
        with self._db.session() as session:
            document = session.get(Document, document_id)
            if document is None or document.tenant_id != tenant_id:
                raise EmbeddingError(
                    EmbeddingErrorType.NOT_FOUND,
                    f"document {document_id!r} not found for tenant {tenant_id!r}",
                )
            session.expunge(document)
            return document

    def _load_chunks(self, document_id: str, tenant_id: str) -> _AssetRef:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(Asset.document_id == document_id, Asset.asset_type == AssetType.CHUNKS)
                .order_by(Asset.version.desc())
                .first()
            )
            if asset is None:
                raise EmbeddingError(
                    EmbeddingErrorType.MISSING_CHUNKS,
                    f"no chunk asset for document {document_id!r}; chunk it first",
                )
            asset_id = asset.id
            version = asset.version
        key = f"{tenant_id}/{document_id}/chunks"
        try:
            content = self._storage.get(key, version=version).decode("utf-8")
        except (KeyError, OSError) as exc:
            raise EmbeddingError(
                EmbeddingErrorType.MISSING_CHUNKS,
                f"chunk payload unavailable for document {document_id!r}",
            ) from exc
        return _AssetRef(asset_id=asset_id, version=version, content=content)

    def _existing_asset(self, document_id: str, content_hash: str) -> tuple[str, int] | None:
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
                asset_type=AssetType.EMBEDDING,
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
                    relation="embedded_from_chunks",
                )
            )
            return asset.id

    def _event(
        self,
        event_type: EmbeddingEventType,
        document_id: str,
        tenant_id: str,
        *,
        asset_id: str | None = None,
        version: int | None = None,
        detail: str = "",
    ) -> EmbeddingEvent:
        return EmbeddingEvent(
            event_type=event_type,
            document_id=document_id,
            tenant_id=tenant_id,
            asset_id=asset_id,
            version=version,
            detail=detail,
        )

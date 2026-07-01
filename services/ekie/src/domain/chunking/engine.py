"""Chunking engine: transforms enriched Markdown into versioned chunk assets.

Reads a document's Markdown and Document Intelligence report, applies the
configured chunk strategy, validates every chunk, and persists the result as an
immutable, versioned managed asset with lineage back to the intelligence asset
(handbook 9.6, 9.16, ADR-018/ADR-020).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from domain.chunking.context import build_context
from domain.chunking.errors import ChunkingError, ChunkingErrorType
from domain.chunking.events import ChunkingEvent, ChunkingEventType
from domain.chunking.models import Chunk, ChunkDocument, ChunkMetadata
from domain.chunking.policy import ChunkingPolicy
from domain.chunking.strategies import ChunkDraft, ChunkStrategyRegistry, default_registry
from domain.chunking.validation import ChunkValidator
from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    Lineage,
)
from domain.intelligence import (
    DocumentIntelligenceReport,
    build_analyzed_document,
    parse_markdown,
)
from domain.storage import AssetStorage, compute_content_hash


@dataclass(frozen=True)
class ChunkingResult:
    """Outcome of chunking a single document."""

    document_id: str
    asset_id: str
    version: int
    storage_uri: str
    content_hash: str
    created: bool
    chunk_document: ChunkDocument
    events: list[ChunkingEvent] = field(default_factory=list)


@dataclass(frozen=True)
class _AssetRef:
    asset_id: str
    version: int
    content: str


class ChunkingEngine:
    """Generates and persists versioned, validated knowledge chunks."""

    def __init__(
        self,
        db: ControlPlaneDatabase,
        storage: AssetStorage,
        policy: ChunkingPolicy,
        *,
        registry: ChunkStrategyRegistry | None = None,
    ) -> None:
        self._db = db
        self._storage = storage
        self._policy = policy
        self._registry = registry or default_registry()
        self._validator = ChunkValidator(policy)

    def chunk(self, document_id: str, tenant_id: str) -> ChunkingResult:
        """Chunk a document's latest Markdown into a versioned chunk asset."""
        events = [self._event(ChunkingEventType.CHUNKING_STARTED, document_id, tenant_id)]
        try:
            document = self._load_document(document_id, tenant_id)
            intelligence = self._load_asset(
                document_id, tenant_id, AssetType.INTELLIGENCE, "intelligence"
            )
            markdown = self._load_asset(
                document_id, tenant_id, AssetType.MARKDOWN, "markdown"
            )
            report = DocumentIntelligenceReport.model_validate_json(intelligence.content)
            chunk_document = self._build_chunks(document, report, markdown.content)
            events.append(
                self._event(
                    ChunkingEventType.CHUNKS_GENERATED,
                    document_id,
                    tenant_id,
                    detail=f"{chunk_document.chunk_count} chunks",
                )
            )
            events.append(self._event(ChunkingEventType.CHUNKS_VALIDATED, document_id, tenant_id))
            return self._persist(document_id, tenant_id, intelligence, chunk_document, events)
        except ChunkingError as exc:
            events.append(
                self._event(
                    ChunkingEventType.CHUNKING_FAILED,
                    document_id,
                    tenant_id,
                    detail=f"{exc.error_type.value}: {exc}",
                )
            )
            raise

    def _build_chunks(
        self, document: Document, report: DocumentIntelligenceReport, markdown_text: str
    ) -> ChunkDocument:
        analyzed = build_analyzed_document(parse_markdown(markdown_text))
        context = build_context(report, analyzed)
        plugin = self._registry.select(self._policy.default_strategy)
        drafts = plugin.generate(context, self._policy)

        known_section_ids = {node.section_id for node in report.structure}
        chunks: list[Chunk] = []
        seen_hashes: set[str] = set()
        sequence = 0
        for draft in drafts:
            self._validate(draft, known_section_ids)
            content_hash = self._hash(draft.content)
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)
            sequence += 1
            chunks.append(
                self._to_chunk(document, report, draft, sequence, content_hash)
            )

        if not chunks:
            raise ChunkingError(
                ChunkingErrorType.EMPTY_RESULT,
                f"no chunks generated for document {document.id!r}",
            )
        return ChunkDocument(
            document_id=document.id,
            markdown_version=report.document_version,
            strategy=self._policy.default_strategy,
            chunk_count=len(chunks),
            total_tokens=sum(chunk.metadata.token_count for chunk in chunks),
            chunks=chunks,
        )

    def _validate(self, draft: ChunkDraft, known_section_ids: set[str]) -> None:
        report = self._validator.validate(draft, known_section_ids)
        if not report.valid:
            raise ChunkingError(
                ChunkingErrorType.VALIDATION_FAILURE, "; ".join(report.messages)
            )

    def _to_chunk(
        self,
        document: Document,
        report: DocumentIntelligenceReport,
        draft: ChunkDraft,
        sequence: int,
        content_hash: str,
    ) -> Chunk:
        metadata = ChunkMetadata(
            chunk_id=f"CHK-{sequence:06d}",
            document_id=document.id,
            markdown_version=report.document_version,
            section_id=draft.section_id,
            section_title=draft.section_title,
            breadcrumb=draft.breadcrumb,
            heading_level=draft.heading_level,
            chunk_sequence=sequence,
            token_count=draft.token_count,
            language=report.language,
            chunk_strategy=self._policy.default_strategy,
            classification=document.classification_clearance,
            contains_table=draft.contains_table,
            contains_code=draft.contains_code,
            contains_image=draft.contains_image,
            quality_score=report.quality.overall,
        )
        return Chunk(content=draft.content, content_hash=content_hash, metadata=metadata)

    def _persist(
        self,
        document_id: str,
        tenant_id: str,
        intelligence: _AssetRef,
        chunk_document: ChunkDocument,
        events: list[ChunkingEvent],
    ) -> ChunkingResult:
        payload = chunk_document.canonical_json()
        content_hash = compute_content_hash(payload)
        key = f"{tenant_id}/{document_id}/chunks"

        existing = self._existing_asset(document_id, content_hash)
        if existing is not None:
            events.append(
                self._event(
                    ChunkingEventType.CHUNKING_SKIPPED,
                    document_id,
                    tenant_id,
                    asset_id=existing[0],
                    version=existing[1],
                    detail="identical chunk set; reusing existing asset",
                )
            )
            return ChunkingResult(
                document_id=document_id,
                asset_id=existing[0],
                version=existing[1],
                storage_uri=f"asset://{key}?version={existing[1]}",
                content_hash=content_hash,
                created=False,
                chunk_document=chunk_document,
                events=events,
            )

        try:
            stored = self._storage.put_next(key, payload)
        except OSError as exc:  # pragma: no cover - local storage rarely fails
            raise ChunkingError(ChunkingErrorType.STORAGE_FAILURE, str(exc)) from exc
        storage_uri = f"asset://{key}?version={stored.version}"
        asset_id = self._record_asset(
            document_id, tenant_id, stored.version, storage_uri, content_hash, intelligence.asset_id
        )
        events.append(
            self._event(
                ChunkingEventType.ASSET_STORED,
                document_id,
                tenant_id,
                asset_id=asset_id,
                version=stored.version,
            )
        )
        return ChunkingResult(
            document_id=document_id,
            asset_id=asset_id,
            version=stored.version,
            storage_uri=storage_uri,
            content_hash=content_hash,
            created=True,
            chunk_document=chunk_document,
            events=events,
        )

    def _load_document(self, document_id: str, tenant_id: str) -> Document:
        with self._db.session() as session:
            document = session.get(Document, document_id)
            if document is None or document.tenant_id != tenant_id:
                raise ChunkingError(
                    ChunkingErrorType.NOT_FOUND,
                    f"document {document_id!r} not found for tenant {tenant_id!r}",
                )
            session.expunge(document)
            return document

    def _load_asset(
        self, document_id: str, tenant_id: str, asset_type: AssetType, suffix: str
    ) -> _AssetRef:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(Asset.document_id == document_id, Asset.asset_type == asset_type)
                .order_by(Asset.version.desc())
                .first()
            )
            if asset is None:
                raise ChunkingError(
                    self._missing_error(asset_type),
                    f"no {asset_type.value} asset for document {document_id!r}",
                )
            asset_id = asset.id
            version = asset.version
        key = f"{tenant_id}/{document_id}/{suffix}"
        try:
            content = self._storage.get(key, version=version).decode("utf-8")
        except (KeyError, OSError) as exc:
            raise ChunkingError(
                self._missing_error(asset_type),
                f"{asset_type.value} payload unavailable for document {document_id!r}",
            ) from exc
        return _AssetRef(asset_id=asset_id, version=version, content=content)

    @staticmethod
    def _missing_error(asset_type: AssetType) -> ChunkingErrorType:
        if asset_type is AssetType.MARKDOWN:
            return ChunkingErrorType.MISSING_MARKDOWN
        return ChunkingErrorType.MISSING_INTELLIGENCE

    def _existing_asset(self, document_id: str, content_hash: str) -> tuple[str, int] | None:
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
    ) -> str:
        with self._db.session() as session:
            asset = Asset(
                document_id=document_id,
                tenant_id=tenant_id,
                asset_type=AssetType.CHUNKS,
                version=version,
                storage_uri=storage_uri,
                content_hash=content_hash,
            )
            session.add(asset)
            session.flush()
            session.add(
                Lineage(
                    asset_id=asset.id,
                    parent_asset_id=parent_asset_id,
                    relation="chunked_from_intelligence",
                )
            )
            return asset.id

    @staticmethod
    def _hash(content: str) -> str:
        return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"

    def _event(
        self,
        event_type: ChunkingEventType,
        document_id: str,
        tenant_id: str,
        *,
        asset_id: str | None = None,
        version: int | None = None,
        detail: str = "",
    ) -> ChunkingEvent:
        return ChunkingEvent(
            event_type=event_type,
            document_id=document_id,
            tenant_id=tenant_id,
            asset_id=asset_id,
            version=version,
            detail=detail,
        )

"""Transformation pipeline: raw document to versioned canonical Markdown asset.

Coordinates parser selection, content extraction, metadata assembly,
normalization, canonical Markdown generation, validation, deduplication, and
immutable versioned asset persistence with Control Plane references and lineage
(handbook Chapter 7). It does not perform chunking or embedding.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from domain.control_plane import Asset, AssetType, ControlPlaneDatabase, Document
from domain.storage import AssetStorage, compute_content_hash
from domain.transformation.errors import TransformationError, TransformationErrorType
from domain.transformation.events import TransformationEvent, TransformationEventType
from domain.transformation.markdown_document import FrontMatter, MarkdownDocument
from domain.transformation.normalization import normalize_text
from domain.transformation.parsers import (
    ParserContext,
    ParserError,
    ParserRegistry,
    UnsupportedFormatError,
    default_registry,
)
from domain.transformation.policy import TransformationPolicy
from domain.transformation.validation import MarkdownValidator


@dataclass(frozen=True)
class TransformationResult:
    """Outcome of transforming a single document into a Markdown asset."""

    document_id: str
    asset_id: str
    version: int
    storage_uri: str
    content_hash: str
    created: bool
    markdown: str
    events: list[TransformationEvent] = field(default_factory=list)


def _extension_of(source_path: str) -> str:
    """Return the lowercase extension of ``source_path`` without the dot."""
    return PurePosixPath(source_path).suffix.lstrip(".").lower()


class TransformationPipeline:
    """Transforms documents into deterministic canonical Markdown assets."""

    STAGE = "transformation"

    def __init__(
        self,
        db: ControlPlaneDatabase,
        storage: AssetStorage,
        policy: TransformationPolicy,
        *,
        registry: ParserRegistry | None = None,
        validator: MarkdownValidator | None = None,
    ) -> None:
        self._db = db
        self._storage = storage
        self._policy = policy
        self._registry = registry or default_registry()
        self._validator = validator or MarkdownValidator()

    def transform(
        self, document_id: str, tenant_id: str, data: bytes, *, mime_type: str | None = None
    ) -> TransformationResult:
        """Transform ``data`` for ``document_id`` into a versioned Markdown asset."""
        events: list[TransformationEvent] = [
            self._event(TransformationEventType.TRANSFORMATION_STARTED, document_id, tenant_id)
        ]
        try:
            document = self._load_document(document_id, tenant_id)
            markdown_doc = self._generate_markdown(document, data, mime_type)
            self._validate(markdown_doc, document_id, tenant_id, events)
            return self._persist(document, markdown_doc, tenant_id, events)
        except TransformationError as exc:
            events.append(
                self._event(
                    TransformationEventType.TRANSFORMATION_FAILED,
                    document_id,
                    tenant_id,
                    detail=f"{exc.error_type.value}: {exc}",
                )
            )
            raise

    def _load_document(self, document_id: str, tenant_id: str) -> Document:
        with self._db.session() as session:
            document = session.get(Document, document_id)
            if document is None or document.tenant_id != tenant_id:
                raise TransformationError(
                    TransformationErrorType.NOT_FOUND,
                    f"document {document_id!r} not found for tenant {tenant_id!r}",
                )
            session.expunge(document)
            return document

    def _generate_markdown(
        self, document: Document, data: bytes, mime_type: str | None
    ) -> MarkdownDocument:
        extension = _extension_of(document.source_path)
        context = ParserContext(
            source_path=document.source_path, extension=extension, mime_type=mime_type
        )
        try:
            parser = self._registry.select(context)
        except UnsupportedFormatError as exc:
            raise TransformationError(
                TransformationErrorType.UNSUPPORTED_FORMAT, str(exc)
            ) from exc
        try:
            parsed = parser.parse(data, context)
        except ParserError as exc:
            raise TransformationError(TransformationErrorType.PARSER_FAILURE, str(exc)) from exc

        body = normalize_text(
            parsed.body,
            normalize_unicode=self._policy.normalize_unicode,
            collapse_blank_lines=self._policy.collapse_blank_lines,
        )
        front_matter = self._build_front_matter(document, parsed.metadata, extension)
        return MarkdownDocument(body=body, front_matter=front_matter)

    def _build_front_matter(
        self, document: Document, metadata: object, source_type: str
    ) -> FrontMatter | None:
        if not self._policy.include_front_matter:
            return None
        language = getattr(metadata, "language", None) or self._policy.default_language
        return FrontMatter(
            document_id=document.id,
            repository_id=document.repository_id,
            version=document.version,
            source_type=source_type or "unknown",
            source_hash=f"sha256:{document.content_hash}",
            language=language,
            title=getattr(metadata, "title", None),
            author=getattr(metadata, "author", None),
        )

    def _validate(
        self,
        markdown_doc: MarkdownDocument,
        document_id: str,
        tenant_id: str,
        events: list[TransformationEvent],
    ) -> None:
        report = self._validator.validate(markdown_doc)
        if not report.is_valid:
            raise TransformationError(
                TransformationErrorType.VALIDATION_FAILURE,
                "; ".join(report.errors),
            )
        events.append(
            self._event(
                TransformationEventType.TRANSFORMATION_VALIDATED, document_id, tenant_id
            )
        )

    def _persist(
        self,
        document: Document,
        markdown_doc: MarkdownDocument,
        tenant_id: str,
        events: list[TransformationEvent],
    ) -> TransformationResult:
        payload = markdown_doc.render_bytes()
        content_hash = compute_content_hash(payload)
        storage_key = f"{tenant_id}/{document.id}/markdown"
        markdown_text = markdown_doc.render()

        existing = self._existing_asset(document.id, content_hash)
        if existing is not None:
            events.append(
                self._event(
                    TransformationEventType.TRANSFORMATION_SKIPPED,
                    document.id,
                    tenant_id,
                    asset_id=existing.asset_id,
                    version=existing.version,
                    detail="identical content hash; reusing existing asset",
                )
            )
            return TransformationResult(
                document_id=document.id,
                asset_id=existing.asset_id,
                version=existing.version,
                storage_uri=existing.storage_uri,
                content_hash=content_hash,
                created=False,
                markdown=markdown_text,
                events=events,
            )

        try:
            stored = self._storage.put_next(storage_key, payload)
        except OSError as exc:  # pragma: no cover - local storage rarely fails
            raise TransformationError(
                TransformationErrorType.STORAGE_FAILURE, str(exc)
            ) from exc
        events.append(
            self._event(
                TransformationEventType.MARKDOWN_GENERATED,
                document.id,
                tenant_id,
                version=stored.version,
            )
        )

        storage_uri = f"asset://{storage_key}?version={stored.version}"
        asset_id = self._record_asset(
            document.id,
            tenant_id,
            stored.version,
            storage_uri,
            content_hash,
            metrics={"markdown_chars": len(markdown_text)},
        )
        events.append(
            self._event(
                TransformationEventType.ASSET_STORED,
                document.id,
                tenant_id,
                asset_id=asset_id,
                version=stored.version,
            )
        )
        return TransformationResult(
            document_id=document.id,
            asset_id=asset_id,
            version=stored.version,
            storage_uri=storage_uri,
            content_hash=content_hash,
            created=True,
            markdown=markdown_text,
            events=events,
        )

    def _existing_asset(self, document_id: str, content_hash: str) -> _AssetRef | None:
        with self._db.session() as session:
            row = (
                session.query(Asset)
                .filter(
                    Asset.document_id == document_id,
                    Asset.asset_type == AssetType.MARKDOWN,
                )
                .order_by(Asset.version.desc())
                .first()
            )
            if row is None or row.content_hash != content_hash:
                return None
            return _AssetRef(
                asset_id=row.id, version=row.version, storage_uri=row.storage_uri
            )

    def _record_asset(
        self,
        document_id: str,
        tenant_id: str,
        version: int,
        storage_uri: str,
        content_hash: str,
        metrics: dict[str, int | float | str] | None = None,
    ) -> str:
        with self._db.session() as session:
            asset = Asset(
                document_id=document_id,
                tenant_id=tenant_id,
                asset_type=AssetType.MARKDOWN,
                version=version,
                storage_uri=storage_uri,
                content_hash=content_hash,
                stage_metrics=json.dumps(metrics) if metrics is not None else None,
            )
            session.add(asset)
            session.flush()
            return asset.id

    def _event(
        self,
        event_type: TransformationEventType,
        document_id: str,
        tenant_id: str,
        *,
        asset_id: str | None = None,
        version: int | None = None,
        detail: str = "",
    ) -> TransformationEvent:
        return TransformationEvent(
            event_type=event_type,
            document_id=document_id,
            tenant_id=tenant_id,
            asset_id=asset_id,
            version=version,
            detail=detail,
        )


@dataclass(frozen=True)
class _AssetRef:
    """Lightweight reference to an existing stored asset."""

    asset_id: str
    version: int
    storage_uri: str

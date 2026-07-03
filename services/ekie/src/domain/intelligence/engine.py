"""Document Intelligence engine: enriches Markdown into a versioned report asset.

Runs the analyzer pipeline over a document's canonical Markdown and persists the
resulting :class:`DocumentIntelligenceReport` as an immutable, versioned managed
asset with lineage back to its source Markdown asset (handbook 8.16, ADR-016).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum

from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    Lineage,
)
from domain.intelligence.analysis import build_analyzed_document
from domain.intelligence.analyzers import (
    Analyzer,
    IntelligenceReportBuilder,
    default_analyzers,
)
from domain.intelligence.events import IntelligenceEvent, IntelligenceEventType
from domain.intelligence.markdown_ast import parse_markdown
from domain.intelligence.models import DocumentIntelligenceReport
from domain.intelligence.policy import IntelligencePolicy
from domain.storage import AssetStorage, compute_content_hash


class IntelligenceErrorType(StrEnum):
    """Categories of intelligence failure for targeted recovery."""

    NOT_FOUND = "not_found"
    MISSING_MARKDOWN = "missing_markdown"
    STORAGE_FAILURE = "storage_failure"


class IntelligenceError(RuntimeError):
    """Raised when a document cannot be enriched into an intelligence asset."""

    def __init__(self, error_type: IntelligenceErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type


@dataclass(frozen=True)
class IntelligenceResult:
    """Outcome of enriching a single document."""

    document_id: str
    asset_id: str
    version: int
    storage_uri: str
    content_hash: str
    created: bool
    report: DocumentIntelligenceReport
    events: list[IntelligenceEvent] = field(default_factory=list)


@dataclass(frozen=True)
class _MarkdownRef:
    asset_id: str
    version: int
    content: str


class DocumentIntelligenceEngine:
    """Enriches canonical Markdown with structural and semantic intelligence."""

    def __init__(
        self,
        db: ControlPlaneDatabase,
        storage: AssetStorage,
        policy: IntelligencePolicy,
        *,
        analyzers: list[Analyzer] | None = None,
    ) -> None:
        self._db = db
        self._storage = storage
        self._policy = policy
        self._analyzers = analyzers or default_analyzers()

    def analyze_markdown(
        self,
        document_id: str,
        document_version: int,
        markdown_text: str,
        policy: IntelligencePolicy | None = None,
    ) -> DocumentIntelligenceReport:
        """Run the analyzer pipeline over ``markdown_text`` and return the report."""
        policy = policy or self._policy
        parsed = parse_markdown(markdown_text)
        analyzed = build_analyzed_document(parsed)
        builder = IntelligenceReportBuilder(language=policy.default_language)
        for analyzer in self._analyzers:
            analyzer.analyze(analyzed, builder, policy)
        quality = builder.quality
        if quality is None:  # pragma: no cover - QualityAnalyzer always runs
            raise IntelligenceError(
                IntelligenceErrorType.STORAGE_FAILURE, "quality analyzer did not run"
            )
        return DocumentIntelligenceReport(
            document_id=document_id,
            document_version=document_version,
            language=builder.language,
            classification=builder.classification,
            structure=analyzed.sections,
            tables=builder.tables,
            figures=builder.figures,
            code_blocks=builder.code_blocks,
            sections=builder.sections,
            sensitive_findings=builder.sensitive_findings,
            quality=quality,
            semantic_metadata=builder.semantic_metadata(len(analyzed.sections)),
        )

    def enrich(
        self,
        document_id: str,
        tenant_id: str,
        *,
        provider_override: str | None = None,
        model_override: str | None = None,
    ) -> IntelligenceResult:
        """Enrich a document's latest Markdown into a versioned report asset."""
        events = [self._event(IntelligenceEventType.INTELLIGENCE_STARTED, document_id, tenant_id)]
        
        policy = self._policy
        if provider_override or model_override:
            updates: dict[str, object] = {"enable_llm_analysis": True}
            if provider_override:
                updates["llm_provider"] = provider_override
            if model_override:
                updates["llm_model"] = model_override
            policy = policy.model_copy(update=updates)
            
        try:
            document = self._load_document(document_id, tenant_id)
            markdown = self._load_markdown(document_id, tenant_id)
            report = self.analyze_markdown(
                document_id, document.version, markdown.content, policy
            )
            return self._persist(document_id, tenant_id, markdown, report, events)
        except IntelligenceError as exc:
            events.append(
                self._event(
                    IntelligenceEventType.INTELLIGENCE_FAILED,
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
                raise IntelligenceError(
                    IntelligenceErrorType.NOT_FOUND,
                    f"document {document_id!r} not found for tenant {tenant_id!r}",
                )
            session.expunge(document)
            return document

    def _load_markdown(self, document_id: str, tenant_id: str) -> _MarkdownRef:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(
                    Asset.document_id == document_id,
                    Asset.asset_type == AssetType.MARKDOWN,
                )
                .order_by(Asset.version.desc())
                .first()
            )
            if asset is None:
                raise IntelligenceError(
                    IntelligenceErrorType.MISSING_MARKDOWN,
                    f"no markdown asset for document {document_id!r}; transform it first",
                )
            asset_id = asset.id
            version = asset.version
        key = f"{tenant_id}/{document_id}/markdown"
        try:
            content = self._storage.get(key, version=version).decode("utf-8")
        except (KeyError, OSError) as exc:
            raise IntelligenceError(
                IntelligenceErrorType.MISSING_MARKDOWN,
                f"markdown payload unavailable for document {document_id!r}",
            ) from exc
        return _MarkdownRef(asset_id=asset_id, version=version, content=content)

    def _persist(
        self,
        document_id: str,
        tenant_id: str,
        markdown: _MarkdownRef,
        report: DocumentIntelligenceReport,
        events: list[IntelligenceEvent],
    ) -> IntelligenceResult:
        payload = report.canonical_json()
        content_hash = compute_content_hash(payload)
        key = f"{tenant_id}/{document_id}/intelligence"

        existing = self._existing_asset(document_id, content_hash)
        if existing is not None:
            events.append(
                self._event(
                    IntelligenceEventType.INTELLIGENCE_SKIPPED,
                    document_id,
                    tenant_id,
                    asset_id=existing[0],
                    version=existing[1],
                    detail="identical report hash; reusing existing asset",
                )
            )
            return IntelligenceResult(
                document_id=document_id,
                asset_id=existing[0],
                version=existing[1],
                storage_uri=f"asset://{key}?version={existing[1]}",
                content_hash=content_hash,
                created=False,
                report=report,
                events=events,
            )

        try:
            stored = self._storage.put_next(key, payload)
        except OSError as exc:  # pragma: no cover - local storage rarely fails
            raise IntelligenceError(IntelligenceErrorType.STORAGE_FAILURE, str(exc)) from exc
        events.append(
            self._event(
                IntelligenceEventType.REPORT_GENERATED,
                document_id,
                tenant_id,
                version=stored.version,
            )
        )
        storage_uri = f"asset://{key}?version={stored.version}"
        asset_id = self._record_asset(
            document_id,
            tenant_id,
            stored.version,
            storage_uri,
            content_hash,
            markdown.asset_id,
            metrics={
                "section_count": report.semantic_metadata.section_count,
                "token_count": report.semantic_metadata.token_count,
                "table_count": len(report.tables),
                "code_block_count": len(report.code_blocks),
                "language": report.semantic_metadata.language,
            },
        )
        events.append(
            self._event(
                IntelligenceEventType.ASSET_STORED,
                document_id,
                tenant_id,
                asset_id=asset_id,
                version=stored.version,
            )
        )
        return IntelligenceResult(
            document_id=document_id,
            asset_id=asset_id,
            version=stored.version,
            storage_uri=storage_uri,
            content_hash=content_hash,
            created=True,
            report=report,
            events=events,
        )

    def _existing_asset(self, document_id: str, content_hash: str) -> tuple[str, int] | None:
        with self._db.session() as session:
            asset = (
                session.query(Asset)
                .filter(
                    Asset.document_id == document_id,
                    Asset.asset_type == AssetType.INTELLIGENCE,
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
                asset_type=AssetType.INTELLIGENCE,
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
                    relation="derived_from_markdown",
                )
            )
            return asset.id

    def _event(
        self,
        event_type: IntelligenceEventType,
        document_id: str,
        tenant_id: str,
        *,
        asset_id: str | None = None,
        version: int | None = None,
        detail: str = "",
    ) -> IntelligenceEvent:
        return IntelligenceEvent(
            event_type=event_type,
            document_id=document_id,
            tenant_id=tenant_id,
            asset_id=asset_id,
            version=version,
            detail=detail,
        )

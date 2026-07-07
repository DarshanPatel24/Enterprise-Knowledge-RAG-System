"""Control Plane ORM models: the single source of truth for ingestion state.

Covers repositories, documents, immutable versioned assets, workflows, asset
lineage, and per-stage processing state. Types are chosen to be portable across
Microsoft SQL Server (production control plane) and SQLite (tests).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _new_id() -> str:
    """Return a new portable string identifier."""
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base for all Control Plane models."""


class RepositoryStatus(StrEnum):
    """Lifecycle status of a synchronized source repository."""

    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class DocumentStatus(StrEnum):
    """Lifecycle status of a document digital twin."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AssetType(StrEnum):
    """Type of an immutable generated asset."""

    MARKDOWN = "markdown"
    INTELLIGENCE = "intelligence"
    CHUNKS = "chunks"
    EMBEDDING = "embedding"
    VECTOR = "vector"


class WorkflowStatus(StrEnum):
    """Execution status of an ingestion workflow."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ProcessingStatus(StrEnum):
    """Status of a single processing stage for a document."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobKind(StrEnum):
    """The kind of work a durable ingestion job performs."""

    INGEST = "ingest"
    DELETE = "delete"


class JobStatus(StrEnum):
    """Lifecycle status of a durable ingestion job."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class TimestampMixin:
    """Adds created and updated timestamps to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False
    )


class Repository(Base, TimestampMixin):
    """A registered enterprise source repository."""

    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[RepositoryStatus] = mapped_column(
        String(32), default=RepositoryStatus.ACTIVE, nullable=False
    )

    documents: Mapped[list[Document]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_repository_tenant_name"),)


class Document(Base, TimestampMixin):
    """A document digital twin tracked in the Control Plane."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    classification_clearance: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        String(32), default=DocumentStatus.ACTIVE, nullable=False
    )

    repository: Mapped[Repository] = relationship(back_populates="documents")
    assets: Mapped[list[Asset]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    workflows: Mapped[list[Workflow]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    processing_states: Mapped[list[ProcessingState]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("repository_id", "source_path", name="uq_document_repo_path"),
    )


class Asset(Base, TimestampMixin):
    """An immutable, versioned generated asset for a document."""

    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    stage_metrics: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    document: Mapped[Document] = relationship(back_populates="assets")
    lineage_out: Mapped[list[Lineage]] = relationship(
        back_populates="asset",
        foreign_keys="Lineage.asset_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "document_id", "asset_type", "version", name="uq_asset_doc_type_version"
        ),
    )


class Lineage(Base):
    """A directed lineage edge between a derived asset and its parent."""

    __tablename__ = "asset_lineage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.id", ondelete="CASCADE"), index=True
    )
    parent_asset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assets.id"), nullable=True
    )
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    asset: Mapped[Asset] = relationship(back_populates="lineage_out", foreign_keys=[asset_id])


class Workflow(Base, TimestampMixin):
    """An ingestion workflow execution record for a document."""

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    workflow_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(
        String(32), default=WorkflowStatus.PENDING, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship(back_populates="workflows")


class ProcessingState(Base, TimestampMixin):
    """The status of a single processing stage for a document."""

    __tablename__ = "processing_state"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(
        String(32), default=ProcessingStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship(back_populates="processing_states")

    __table_args__ = (
        UniqueConstraint("document_id", "stage", name="uq_processing_doc_stage"),
    )


class IngestionJob(Base, TimestampMixin):
    """A durable unit of ingestion work processed asynchronously by a worker pool.

    Jobs are intentionally decoupled from the ``documents`` table (no foreign
    key) so a ``delete`` job can outlive the document row it removes and still
    record its terminal outcome. Idempotency and deduplication key on
    ``(tenant_id, document_id, kind, content_hash)`` for jobs that are not yet
    terminal.
    """

    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    kind: Mapped[JobKind] = mapped_column(String(16), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        String(16), default=JobStatus.QUEUED, nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    source_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False, index=True
    )
    locked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    intelligence_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intelligence_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    embedding_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    force: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngestionSource(Base, TimestampMixin):
    """Raw source bytes for an asynchronous ingestion job.

    Async ingestion executes in a worker process separate from the API, so the
    source payload must be handed off through shared, durable storage rather than
    per-process memory. The Control Plane database is the shared source of truth,
    so the bytes are staged here (keyed by tenant and document) until the worker
    consumes them.
    """

    __tablename__ = "ingestion_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "document_id", name="uq_source_tenant_doc"),
    )

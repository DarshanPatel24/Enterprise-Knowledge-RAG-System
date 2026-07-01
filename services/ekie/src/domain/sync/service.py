"""Repository synchronizer: the ingestion entry point (EKIE handbook Chapter 6).

Coordinates a connector, policy filtering, content hashing, change detection,
and Digital Twin persistence in the Control Plane, emitting standardized
synchronization events. It does not transform documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from domain.control_plane import (
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
    Repository,
    RepositoryStatus,
)
from domain.storage import compute_content_hash
from domain.sync.change_detection import (
    ChangeDetector,
    ChangeType,
    DetectedChange,
    InventoryItem,
    TwinDocument,
)
from domain.sync.connectors import ConnectorError, RepositoryConnector
from domain.sync.events import SyncEvent, SyncEventType
from domain.sync.policy import ScanStrategy, SyncPolicy
from domain.sync.retry import RetryPolicy, run_with_retry
from domain.sync.state_machine import RepositorySyncState, assert_repository_transition


class SynchronizationError(RuntimeError):
    """Raised when synchronization cannot complete after recovery attempts."""


@dataclass(frozen=True)
class SyncResult:
    """Outcome of a single synchronization run."""

    repository_id: str
    final_state: RepositorySyncState
    changes: list[DetectedChange] = field(default_factory=list)
    events: list[SyncEvent] = field(default_factory=list)

    def count(self, change_type: ChangeType) -> int:
        """Return the number of detected changes of a given type."""
        return sum(1 for change in self.changes if change.change_type == change_type)


def register_repository(
    db: ControlPlaneDatabase,
    *,
    tenant_id: str,
    name: str,
    source_type: str,
    uri: str,
) -> str:
    """Register a repository in the Control Plane and return its id."""
    with db.session() as session:
        repository = Repository(
            tenant_id=tenant_id,
            name=name,
            source_type=source_type,
            uri=uri,
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repository)
        session.flush()
        return repository.id


class RepositorySynchronizer:
    """Synchronizes one repository into the Control Plane Digital Twin."""

    def __init__(
        self,
        db: ControlPlaneDatabase,
        connector: RepositoryConnector,
        policy: SyncPolicy,
        *,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._db = db
        self._connector = connector
        self._policy = policy
        self._retry_policy = retry_policy or RetryPolicy()
        self._detector = ChangeDetector(
            rename_detection_enabled=policy.rename_detection_enabled
        )

    def synchronize(
        self, repository_id: str, tenant_id: str, *, strategy: ScanStrategy | None = None
    ) -> SyncResult:
        """Scan the repository and reconcile the Digital Twin, emitting events."""
        scan_strategy = strategy or self._policy.scan_strategy
        events: list[SyncEvent] = []
        state = RepositorySyncState.REGISTERED
        try:
            state = self._advance(state, RepositorySyncState.CONNECTING)
            run_with_retry(
                self._connector.connect,
                policy=self._retry_policy,
                retryable=ConnectorError,
            )

            state = self._advance(state, RepositorySyncState.DISCOVERING)
            inventory = self._build_inventory()

            state = self._advance(state, RepositorySyncState.SYNCHRONIZING)
            twins = self._load_twins(repository_id)
            changes = self._detector.detect(inventory, twins)
            events = self._apply_changes(repository_id, tenant_id, changes)

            state = self._advance(state, RepositorySyncState.ACTIVE)
            events.append(
                SyncEvent(
                    event_type=(
                        SyncEventType.REPOSITORY_RECONCILED
                        if scan_strategy is ScanStrategy.FULL
                        else SyncEventType.REPOSITORY_SYNCHRONIZED
                    ),
                    repository_id=repository_id,
                    tenant_id=tenant_id,
                    detail=f"strategy={scan_strategy.value}",
                )
            )
            return SyncResult(
                repository_id=repository_id,
                final_state=state,
                changes=changes,
                events=events,
            )
        except ConnectorError as exc:
            failure = SyncEvent(
                event_type=SyncEventType.SYNCHRONIZATION_FAILED,
                repository_id=repository_id,
                tenant_id=tenant_id,
                detail=str(exc),
            )
            events.append(failure)
            raise SynchronizationError(str(exc)) from exc

    def _advance(
        self, current: RepositorySyncState, target: RepositorySyncState
    ) -> RepositorySyncState:
        assert_repository_transition(current, target)
        return target

    def _build_inventory(self) -> list[InventoryItem]:
        discovered = run_with_retry(
            lambda: list(self._connector.discover()),
            policy=self._retry_policy,
            retryable=ConnectorError,
        )
        inventory: list[InventoryItem] = []
        for obj in discovered:
            if not self._policy.is_included(
                extension=obj.extension,
                size_bytes=obj.size_bytes,
                is_hidden=obj.is_hidden,
                name=obj.name,
            ):
                continue
            source_path = obj.source_path

            def _read(path: str = source_path) -> bytes:
                return self._connector.read_bytes(path)

            data = run_with_retry(
                _read,
                policy=self._retry_policy,
                retryable=ConnectorError,
            )
            inventory.append(
                InventoryItem(
                    source_path=obj.source_path,
                    content_hash=compute_content_hash(data),
                    size_bytes=obj.size_bytes,
                )
            )
        return inventory

    def _load_twins(self, repository_id: str) -> list[TwinDocument]:
        with self._db.session() as session:
            rows = (
                session.query(Document)
                .filter(
                    Document.repository_id == repository_id,
                    Document.status != DocumentStatus.DELETED,
                )
                .all()
            )
            return [
                TwinDocument(
                    document_id=row.id,
                    source_path=row.source_path,
                    content_hash=row.content_hash,
                    version=row.version,
                )
                for row in rows
            ]

    def _apply_changes(
        self, repository_id: str, tenant_id: str, changes: list[DetectedChange]
    ) -> list[SyncEvent]:
        events: list[SyncEvent] = []
        with self._db.session() as session:
            for change in changes:
                event = self._apply_single(session, repository_id, tenant_id, change)
                if event is not None:
                    events.append(event)
        return events

    def _apply_single(
        self,
        session: Session,
        repository_id: str,
        tenant_id: str,
        change: DetectedChange,
    ) -> SyncEvent | None:
        if change.change_type is ChangeType.UNCHANGED:
            return None
        if change.change_type is ChangeType.CREATED:
            return self._apply_created(session, repository_id, tenant_id, change)
        if change.change_type is ChangeType.MODIFIED:
            return self._apply_modified(session, repository_id, tenant_id, change)
        if change.change_type in (ChangeType.RENAMED, ChangeType.MOVED):
            return self._apply_relocation(session, repository_id, tenant_id, change)
        if change.change_type is ChangeType.DELETED:
            return self._apply_deleted(session, repository_id, tenant_id, change)
        return None

    def _apply_created(
        self, session: Session, repository_id: str, tenant_id: str, change: DetectedChange
    ) -> SyncEvent:
        document = Document(
            repository_id=repository_id,
            tenant_id=tenant_id,
            source_path=change.source_path,
            content_hash=change.content_hash or "",
            classification_clearance=self._policy.default_classification,
            version=1,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return SyncEvent(
            event_type=SyncEventType.DOCUMENT_DISCOVERED,
            repository_id=repository_id,
            tenant_id=tenant_id,
            document_id=document.id,
            source_path=change.source_path,
            version=1,
        )

    def _apply_modified(
        self, session: Session, repository_id: str, tenant_id: str, change: DetectedChange
    ) -> SyncEvent:
        document = session.get(Document, change.document_id)
        if document is None:
            raise SynchronizationError(f"twin not found for modify: {change.document_id}")
        document.version += 1
        document.content_hash = change.content_hash or document.content_hash
        return SyncEvent(
            event_type=SyncEventType.DOCUMENT_MODIFIED,
            repository_id=repository_id,
            tenant_id=tenant_id,
            document_id=document.id,
            source_path=change.source_path,
            version=document.version,
        )

    def _apply_relocation(
        self, session: Session, repository_id: str, tenant_id: str, change: DetectedChange
    ) -> SyncEvent:
        document = session.get(Document, change.document_id)
        if document is None:
            raise SynchronizationError(f"twin not found for relocation: {change.document_id}")
        document.source_path = change.source_path
        event_type = (
            SyncEventType.DOCUMENT_RENAMED
            if change.change_type is ChangeType.RENAMED
            else SyncEventType.DOCUMENT_MOVED
        )
        return SyncEvent(
            event_type=event_type,
            repository_id=repository_id,
            tenant_id=tenant_id,
            document_id=document.id,
            source_path=change.source_path,
            previous_path=change.previous_path,
            version=document.version,
        )

    def _apply_deleted(
        self, session: Session, repository_id: str, tenant_id: str, change: DetectedChange
    ) -> SyncEvent | None:
        if not self._policy.delete_propagation_enabled:
            return None
        document = session.get(Document, change.document_id)
        if document is None:
            raise SynchronizationError(f"twin not found for delete: {change.document_id}")
        document.status = DocumentStatus.DELETED
        return SyncEvent(
            event_type=SyncEventType.DOCUMENT_DELETED,
            repository_id=repository_id,
            tenant_id=tenant_id,
            document_id=document.id,
            source_path=change.source_path,
        )

"""Integration tests for the repository synchronizer against SQLite + temp FS."""

from pathlib import Path

from domain.control_plane import ControlPlaneDatabase, Document, DocumentStatus
from domain.sync import (
    ChangeType,
    LocalFileSystemConnector,
    RepositoryConnectorConfig,
    RepositorySynchronizer,
    SyncEventType,
    SyncPolicy,
    register_repository,
)


def _connector(repository_id: str, root: Path) -> LocalFileSystemConnector:
    config = RepositoryConnectorConfig(
        repository_id=repository_id,
        tenant_id="tenant-a",
        name="local",
        connector_type="local_fs",
        root_uri=str(root),
    )
    return LocalFileSystemConnector(config)


def _synchronizer(
    db: ControlPlaneDatabase, repository_id: str, root: Path
) -> RepositorySynchronizer:
    return RepositorySynchronizer(db, _connector(repository_id, root), SyncPolicy())


def test_initial_scan_creates_twins(
    control_plane_db: ControlPlaneDatabase, tmp_path: Path
) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.txt").write_text("alpha")
    (tmp_path / "b.txt").write_text("bravo")

    repository_id = register_repository(
        control_plane_db,
        tenant_id="tenant-a",
        name="repo",
        source_type="local_fs",
        uri=str(tmp_path),
    )
    result = _synchronizer(control_plane_db, repository_id, tmp_path).synchronize(
        repository_id, "tenant-a"
    )

    assert result.count(ChangeType.CREATED) == 2
    event_types = {event.event_type for event in result.events}
    assert SyncEventType.DOCUMENT_DISCOVERED in event_types
    assert SyncEventType.REPOSITORY_SYNCHRONIZED in event_types

    with control_plane_db.session() as session:
        docs = session.query(Document).all()
        assert {d.source_path for d in docs} == {"docs/a.txt", "b.txt"}
        assert all(d.version == 1 for d in docs)
        assert all(d.status == DocumentStatus.ACTIVE for d in docs)


def test_modification_bumps_version(
    control_plane_db: ControlPlaneDatabase, tmp_path: Path
) -> None:
    target = tmp_path / "a.txt"
    target.write_text("v1")
    repository_id = register_repository(
        control_plane_db,
        tenant_id="tenant-a",
        name="repo",
        source_type="local_fs",
        uri=str(tmp_path),
    )
    sync = _synchronizer(control_plane_db, repository_id, tmp_path)
    sync.synchronize(repository_id, "tenant-a")

    target.write_text("v2 content changed")
    result = sync.synchronize(repository_id, "tenant-a")

    assert result.count(ChangeType.MODIFIED) == 1
    assert any(e.event_type is SyncEventType.DOCUMENT_MODIFIED for e in result.events)
    with control_plane_db.session() as session:
        doc = session.query(Document).filter(Document.source_path == "a.txt").one()
        assert doc.version == 2


def test_rename_preserves_identity(
    control_plane_db: ControlPlaneDatabase, tmp_path: Path
) -> None:
    (tmp_path / "old.txt").write_text("stable content")
    repository_id = register_repository(
        control_plane_db,
        tenant_id="tenant-a",
        name="repo",
        source_type="local_fs",
        uri=str(tmp_path),
    )
    sync = _synchronizer(control_plane_db, repository_id, tmp_path)
    sync.synchronize(repository_id, "tenant-a")
    with control_plane_db.session() as session:
        original_id = session.query(Document).one().id

    (tmp_path / "old.txt").rename(tmp_path / "new.txt")
    result = sync.synchronize(repository_id, "tenant-a")

    assert result.count(ChangeType.RENAMED) == 1
    with control_plane_db.session() as session:
        doc = session.query(Document).one()
        assert doc.id == original_id
        assert doc.source_path == "new.txt"


def test_delete_marks_twin_deleted(
    control_plane_db: ControlPlaneDatabase, tmp_path: Path
) -> None:
    (tmp_path / "gone.txt").write_text("temporary")
    repository_id = register_repository(
        control_plane_db,
        tenant_id="tenant-a",
        name="repo",
        source_type="local_fs",
        uri=str(tmp_path),
    )
    sync = _synchronizer(control_plane_db, repository_id, tmp_path)
    sync.synchronize(repository_id, "tenant-a")

    (tmp_path / "gone.txt").unlink()
    result = sync.synchronize(repository_id, "tenant-a")

    assert result.count(ChangeType.DELETED) == 1
    assert any(e.event_type is SyncEventType.DOCUMENT_DELETED for e in result.events)
    with control_plane_db.session() as session:
        doc = session.query(Document).one()
        assert doc.status == DocumentStatus.DELETED


def test_idempotent_rescan_reports_no_changes(
    control_plane_db: ControlPlaneDatabase, tmp_path: Path
) -> None:
    (tmp_path / "a.txt").write_text("unchanged")
    repository_id = register_repository(
        control_plane_db,
        tenant_id="tenant-a",
        name="repo",
        source_type="local_fs",
        uri=str(tmp_path),
    )
    sync = _synchronizer(control_plane_db, repository_id, tmp_path)
    sync.synchronize(repository_id, "tenant-a")
    result = sync.synchronize(repository_id, "tenant-a")

    assert result.count(ChangeType.CREATED) == 0
    assert result.count(ChangeType.MODIFIED) == 0
    assert result.count(ChangeType.UNCHANGED) == 1

"""Integration tests for the transformation pipeline against SQLite + storage."""

import pytest

from domain.control_plane import (
    Asset,
    AssetType,
    ControlPlaneDatabase,
    Document,
    DocumentStatus,
)
from domain.storage import InMemoryAssetStorage
from domain.transformation import (
    TransformationError,
    TransformationErrorType,
    TransformationEventType,
    TransformationPipeline,
    TransformationPolicy,
)


def _register_repository(db: ControlPlaneDatabase) -> str:
    from domain.control_plane import Repository, RepositoryStatus

    with db.session() as session:
        repo = Repository(
            tenant_id="tenant-a",
            name="repo",
            source_type="local_fs",
            uri="local://repo",
            status=RepositoryStatus.ACTIVE,
        )
        session.add(repo)
        session.flush()
        return repo.id


def _add_document(
    db: ControlPlaneDatabase,
    repository_id: str,
    *,
    source_path: str,
    content_hash: str,
    version: int = 1,
) -> str:
    with db.session() as session:
        document = Document(
            repository_id=repository_id,
            tenant_id="tenant-a",
            source_path=source_path,
            content_hash=content_hash,
            classification_clearance="internal",
            version=version,
            status=DocumentStatus.ACTIVE,
        )
        session.add(document)
        session.flush()
        return document.id


def _pipeline(db: ControlPlaneDatabase) -> TransformationPipeline:
    return TransformationPipeline(db, InMemoryAssetStorage(), TransformationPolicy())


def test_transform_creates_versioned_markdown_asset(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    repository_id = _register_repository(control_plane_db)
    document_id = _add_document(
        control_plane_db, repository_id, source_path="docs/a.txt", content_hash="hash-a"
    )
    result = _pipeline(control_plane_db).transform(document_id, "tenant-a", b"Hello world")

    assert result.created is True
    assert result.version == 1
    assert "document_id: " in result.markdown
    assert "Hello world" in result.markdown
    assert result.storage_uri.endswith("version=1")

    event_types = {event.event_type for event in result.events}
    assert TransformationEventType.ASSET_STORED in event_types
    assert TransformationEventType.TRANSFORMATION_VALIDATED in event_types

    with control_plane_db.session() as session:
        asset = session.query(Asset).one()
        assert asset.asset_type == AssetType.MARKDOWN
        assert asset.version == 1
        assert asset.content_hash == result.content_hash


def test_transform_is_deterministic_and_deduplicates(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    repository_id = _register_repository(control_plane_db)
    document_id = _add_document(
        control_plane_db, repository_id, source_path="docs/a.txt", content_hash="hash-a"
    )
    pipeline = _pipeline(control_plane_db)

    first = pipeline.transform(document_id, "tenant-a", b"Same content")
    second = pipeline.transform(document_id, "tenant-a", b"Same content")

    assert first.markdown == second.markdown
    assert first.content_hash == second.content_hash
    assert second.created is False
    assert second.version == first.version
    assert any(
        e.event_type is TransformationEventType.TRANSFORMATION_SKIPPED for e in second.events
    )
    with control_plane_db.session() as session:
        assert session.query(Asset).count() == 1


def test_transform_new_version_on_content_change(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    repository_id = _register_repository(control_plane_db)
    document_id = _add_document(
        control_plane_db, repository_id, source_path="docs/a.txt", content_hash="hash-a"
    )
    pipeline = _pipeline(control_plane_db)
    pipeline.transform(document_id, "tenant-a", b"Version one")

    with control_plane_db.session() as session:
        document = session.get(Document, document_id)
        assert document is not None
        document.version = 2
        document.content_hash = "hash-b"

    result = pipeline.transform(document_id, "tenant-a", b"Version two changed")

    assert result.created is True
    assert result.version == 2
    assert "version: 2" in result.markdown
    with control_plane_db.session() as session:
        assert session.query(Asset).count() == 2


def test_unsupported_format_raises(control_plane_db: ControlPlaneDatabase) -> None:
    repository_id = _register_repository(control_plane_db)
    document_id = _add_document(
        control_plane_db, repository_id, source_path="docs/archive.zip", content_hash="h"
    )
    with pytest.raises(TransformationError) as exc_info:
        _pipeline(control_plane_db).transform(document_id, "tenant-a", b"binary")
    assert exc_info.value.error_type is TransformationErrorType.UNSUPPORTED_FORMAT


def test_missing_document_raises_not_found(control_plane_db: ControlPlaneDatabase) -> None:
    with pytest.raises(TransformationError) as exc_info:
        _pipeline(control_plane_db).transform("missing-id", "tenant-a", b"data")
    assert exc_info.value.error_type is TransformationErrorType.NOT_FOUND


def test_markdown_document_passes_through_pipeline(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    repository_id = _register_repository(control_plane_db)
    document_id = _add_document(
        control_plane_db, repository_id, source_path="docs/page.md", content_hash="h"
    )
    markdown = b"# Report\n\nBody text\n"
    result = _pipeline(control_plane_db).transform(document_id, "tenant-a", markdown)
    assert "# Report" in result.markdown
    assert "Body text" in result.markdown

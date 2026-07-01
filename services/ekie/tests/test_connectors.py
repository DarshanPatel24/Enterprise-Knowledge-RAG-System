"""Tests for the local file system connector and connector registry."""

from pathlib import Path

import pytest

from domain.sync.connectors import (
    ConnectorError,
    LocalFileSystemConnector,
    RepositoryConnectorConfig,
    default_registry,
)


def _config(root: Path) -> RepositoryConnectorConfig:
    return RepositoryConnectorConfig(
        repository_id="repo-1",
        tenant_id="tenant-a",
        name="local",
        connector_type="local_fs",
        root_uri=str(root),
    )


def test_discover_lists_files_with_posix_paths(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.txt").write_text("hello")
    (tmp_path / "b.md").write_text("# title")

    connector = LocalFileSystemConnector(_config(tmp_path))
    connector.connect()
    objects = {obj.source_path: obj for obj in connector.discover()}

    assert set(objects) == {"docs/a.txt", "b.md"}
    assert objects["b.md"].extension == "md"
    assert objects["docs/a.txt"].size_bytes == len("hello")


def test_read_bytes_returns_content(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("payload")
    connector = LocalFileSystemConnector(_config(tmp_path))
    connector.connect()
    assert connector.read_bytes("a.txt") == b"payload"


def test_connect_rejects_missing_root(tmp_path: Path) -> None:
    connector = LocalFileSystemConnector(_config(tmp_path / "absent"))
    with pytest.raises(ConnectorError):
        connector.connect()


def test_read_bytes_blocks_path_traversal(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("payload")
    connector = LocalFileSystemConnector(_config(tmp_path))
    connector.connect()
    with pytest.raises(ConnectorError):
        connector.read_bytes("../../etc/passwd")


def test_registry_creates_local_fs_connector(tmp_path: Path) -> None:
    registry = default_registry()
    assert "local_fs" in registry.registered_types()
    connector = registry.create(_config(tmp_path))
    assert isinstance(connector, LocalFileSystemConnector)


def test_registry_rejects_unknown_type(tmp_path: Path) -> None:
    registry = default_registry()
    config = RepositoryConnectorConfig(
        repository_id="repo-1",
        tenant_id="tenant-a",
        name="x",
        connector_type="does_not_exist",
        root_uri=str(tmp_path),
    )
    with pytest.raises(ValueError):
        registry.create(config)

"""Local file system repository connector (Phase 1, local-first).

Discovers files under a root directory and reads their bytes for hashing. All
path resolution is guarded against directory traversal so a malicious or
malformed ``source_path`` cannot escape the configured repository root.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from domain.sync.connectors.base import (
    ConnectorCapabilities,
    ConnectorError,
    DiscoveredObject,
    RepositoryConnector,
    RepositoryConnectorConfig,
)


class LocalFileSystemConnector(RepositoryConnector):
    """Connector for a local directory tree."""

    connector_type = "local_fs"

    def __init__(self, config: RepositoryConnectorConfig) -> None:
        super().__init__(config)
        self._root = Path(config.root_uri).resolve()

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(supports_incremental=True, supports_event_notifications=False)

    def connect(self) -> None:
        if not self._root.exists() or not self._root.is_dir():
            raise ConnectorError(f"repository root is not a directory: {self._root}")

    def discover(self) -> Iterator[DiscoveredObject]:
        for dirpath, _dirnames, filenames in os.walk(self._root):
            for filename in filenames:
                absolute = Path(dirpath) / filename
                relative = absolute.relative_to(self._root)
                source_path = PurePosixPath(*relative.parts).as_posix()
                stat = absolute.stat()
                yield DiscoveredObject(
                    source_path=source_path,
                    name=filename,
                    extension=absolute.suffix.lower().lstrip("."),
                    size_bytes=stat.st_size,
                    modified_time=datetime.fromtimestamp(stat.st_mtime, UTC),
                    is_hidden=any(part.startswith(".") for part in relative.parts),
                )

    def read_bytes(self, source_path: str) -> bytes:
        resolved = self._safe_resolve(source_path)
        try:
            return resolved.read_bytes()
        except OSError as exc:
            raise ConnectorError(f"failed to read {source_path}: {exc}") from exc

    def _safe_resolve(self, source_path: str) -> Path:
        """Resolve ``source_path`` under the root, rejecting traversal attempts."""
        candidate = (self._root / PurePosixPath(source_path)).resolve()
        if candidate != self._root and self._root not in candidate.parents:
            raise ConnectorError(f"path escapes repository root: {source_path}")
        return candidate

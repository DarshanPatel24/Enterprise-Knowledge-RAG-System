"""Change detection via content hashing (EKIE handbook Chapters 5.13, 6.10-6.14).

Compares the current repository inventory against the existing Digital Twin
state and classifies each difference. Document identity is preserved across
renames and moves: a file whose content hash matches a known twin at a vanished
path is reported as a rename or move, never as a delete plus create.

This module is pure (no I/O, no database) so change classification is fully
deterministic and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath


class ChangeType(StrEnum):
    """Classification of a detected repository change."""

    CREATED = "created"
    MODIFIED = "modified"
    RENAMED = "renamed"
    MOVED = "moved"
    DELETED = "deleted"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class InventoryItem:
    """A current repository object with its computed content hash."""

    source_path: str
    content_hash: str
    size_bytes: int


@dataclass(frozen=True)
class TwinDocument:
    """The existing Digital Twin view of a document (from the Control Plane)."""

    document_id: str
    source_path: str
    content_hash: str
    version: int


@dataclass(frozen=True)
class DetectedChange:
    """A single classified change between inventory and twin state."""

    change_type: ChangeType
    source_path: str
    content_hash: str | None = None
    document_id: str | None = None
    previous_path: str | None = None
    size_bytes: int | None = None


def _parent(source_path: str) -> str:
    """Return the parent folder of a POSIX-style path."""
    return str(PurePosixPath(source_path).parent)


class ChangeDetector:
    """Classifies differences between current inventory and twin state."""

    def __init__(self, *, rename_detection_enabled: bool = True) -> None:
        self._rename_detection_enabled = rename_detection_enabled

    def detect(
        self,
        inventory: list[InventoryItem],
        twins: list[TwinDocument],
    ) -> list[DetectedChange]:
        """Return the ordered list of changes required to reconcile twin state."""
        inventory_by_path = {item.source_path: item for item in inventory}
        twins_by_path = {twin.source_path: twin for twin in twins}

        changes: list[DetectedChange] = []
        consumed_twin_ids: set[str] = set()

        new_items: list[InventoryItem] = []
        for item in inventory:
            twin = twins_by_path.get(item.source_path)
            if twin is None:
                new_items.append(item)
                continue
            consumed_twin_ids.add(twin.document_id)
            if twin.content_hash == item.content_hash:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.UNCHANGED,
                        source_path=item.source_path,
                        content_hash=item.content_hash,
                        document_id=twin.document_id,
                        size_bytes=item.size_bytes,
                    )
                )
            else:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.MODIFIED,
                        source_path=item.source_path,
                        content_hash=item.content_hash,
                        document_id=twin.document_id,
                        size_bytes=item.size_bytes,
                    )
                )

        # Candidate twins for rename/move: known content hashes at paths that
        # no longer exist in the current inventory.
        vanished_by_hash: dict[str, TwinDocument] = {
            twin.content_hash: twin
            for twin in twins
            if twin.document_id not in consumed_twin_ids
            and twin.source_path not in inventory_by_path
        }

        for item in new_items:
            twin = (
                vanished_by_hash.get(item.content_hash)
                if self._rename_detection_enabled
                else None
            )
            if twin is not None and twin.document_id not in consumed_twin_ids:
                consumed_twin_ids.add(twin.document_id)
                change_type = (
                    ChangeType.RENAMED
                    if _parent(twin.source_path) == _parent(item.source_path)
                    else ChangeType.MOVED
                )
                changes.append(
                    DetectedChange(
                        change_type=change_type,
                        source_path=item.source_path,
                        content_hash=item.content_hash,
                        document_id=twin.document_id,
                        previous_path=twin.source_path,
                        size_bytes=item.size_bytes,
                    )
                )
            else:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.CREATED,
                        source_path=item.source_path,
                        content_hash=item.content_hash,
                        size_bytes=item.size_bytes,
                    )
                )

        for twin in twins:
            if twin.document_id not in consumed_twin_ids:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.DELETED,
                        source_path=twin.source_path,
                        document_id=twin.document_id,
                    )
                )

        return changes

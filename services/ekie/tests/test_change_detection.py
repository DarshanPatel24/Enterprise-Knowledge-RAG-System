"""Tests for the change detection engine (pure, no I/O)."""

from domain.sync.change_detection import (
    ChangeDetector,
    ChangeType,
    InventoryItem,
    TwinDocument,
)


def _detect(inventory, twins, *, rename=True):
    detector = ChangeDetector(rename_detection_enabled=rename)
    return {change.source_path: change for change in detector.detect(inventory, twins)}


def test_created_when_path_is_new() -> None:
    inventory = [InventoryItem("docs/a.txt", "hash-a", 10)]
    changes = _detect(inventory, [])
    assert changes["docs/a.txt"].change_type is ChangeType.CREATED


def test_unchanged_when_hash_matches() -> None:
    inventory = [InventoryItem("docs/a.txt", "hash-a", 10)]
    twins = [TwinDocument("id-1", "docs/a.txt", "hash-a", 1)]
    changes = _detect(inventory, twins)
    assert changes["docs/a.txt"].change_type is ChangeType.UNCHANGED
    assert changes["docs/a.txt"].document_id == "id-1"


def test_modified_when_hash_differs() -> None:
    inventory = [InventoryItem("docs/a.txt", "hash-b", 12)]
    twins = [TwinDocument("id-1", "docs/a.txt", "hash-a", 1)]
    changes = _detect(inventory, twins)
    change = changes["docs/a.txt"]
    assert change.change_type is ChangeType.MODIFIED
    assert change.document_id == "id-1"


def test_renamed_same_folder_preserves_identity() -> None:
    inventory = [InventoryItem("docs/new.txt", "hash-a", 10)]
    twins = [TwinDocument("id-1", "docs/old.txt", "hash-a", 1)]
    changes = _detect(inventory, twins)
    change = changes["docs/new.txt"]
    assert change.change_type is ChangeType.RENAMED
    assert change.document_id == "id-1"
    assert change.previous_path == "docs/old.txt"


def test_moved_when_folder_changes() -> None:
    inventory = [InventoryItem("archive/a.txt", "hash-a", 10)]
    twins = [TwinDocument("id-1", "docs/a.txt", "hash-a", 1)]
    changes = _detect(inventory, twins)
    change = changes["archive/a.txt"]
    assert change.change_type is ChangeType.MOVED
    assert change.previous_path == "docs/a.txt"


def test_deleted_when_twin_missing_from_inventory() -> None:
    changes = _detect([], [TwinDocument("id-1", "docs/a.txt", "hash-a", 1)])
    assert changes["docs/a.txt"].change_type is ChangeType.DELETED
    assert changes["docs/a.txt"].document_id == "id-1"


def test_rename_detection_disabled_yields_create_plus_delete() -> None:
    inventory = [InventoryItem("docs/new.txt", "hash-a", 10)]
    twins = [TwinDocument("id-1", "docs/old.txt", "hash-a", 1)]
    changes = _detect(inventory, twins, rename=False)
    assert changes["docs/new.txt"].change_type is ChangeType.CREATED
    assert changes["docs/old.txt"].change_type is ChangeType.DELETED

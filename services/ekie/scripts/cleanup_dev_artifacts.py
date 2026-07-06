"""Remove local development artifacts before production deployment.

Safe to run repeatedly. Never deletes .env, source code, model cache, or the
storage/ directory itself — only time-stamped JSON reports, local Qdrant state
files, Python bytecode caches, and tool-specific cache directories.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]

_JSON_REPORT_GLOBS = [
    "storage/acceptance_report_*.json",
    "storage/qdrant_delete_validation_*.json",
    "storage/qdrant_delete_validation_*",
    "services/ekie/storage/acceptance_report_*.json",
    "services/ekie/storage/qdrant_delete_validation_*.json",
]

_DIR_PATTERNS_RELATIVE = [
    "storage/qdrant",
    "services/ekie/storage",   # mis-routed output directory from earlier runs
]

_RECURSIVE_DIRS = [
    "**/__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]


def _remove_file(path: Path) -> None:
    if path.exists():
        path.unlink()
        print(f"  deleted  {path.relative_to(_SERVICE_ROOT)}")


def _remove_dir(path: Path) -> None:
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        print(f"  removed  {path.relative_to(_SERVICE_ROOT)}")


def main() -> int:
    print("EKIE pre-production cleanup")
    print(f"  root: {_SERVICE_ROOT}\n")

    removed = 0

    # Time-stamped JSON report files.
    for pattern in _JSON_REPORT_GLOBS:
        for match in _SERVICE_ROOT.glob(pattern):
            _remove_file(match)
            removed += 1

    # Local Qdrant state and mis-routed storage directories.
    for rel in _DIR_PATTERNS_RELATIVE:
        candidate = _SERVICE_ROOT / rel
        _remove_dir(candidate)
        removed += 1

    # Recursive cache directories.
    for dir_pattern in _RECURSIVE_DIRS:
        for match in _SERVICE_ROOT.rglob(dir_pattern.lstrip("*/")):
            if match.is_dir():
                _remove_dir(match)
                removed += 1

    print(f"\n  {removed} items processed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

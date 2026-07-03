"""One-command cwd-safe launcher for the EKIE production sync worker.

Changes to the services/ekie directory before running so that settings.py
can locate .env regardless of where the command is invoked from.

Usage:
    python services/ekie/scripts/start_worker.py
    # or after pip install -e services/ekie[...]:
    ekie-worker
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _SERVICE_ROOT.parents[1]
_SYNC_SCRIPT = _SERVICE_ROOT / "scripts" / "production_sync.py"


def _venv_python() -> str:
    """Return the venv Python if it exists, otherwise fall back to sys.executable."""
    candidates = [
        _REPO_ROOT / ".venv" / "Scripts" / "python.exe",   # Windows
        _REPO_ROOT / ".venv" / "bin" / "python",            # Linux/macOS
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def main() -> None:
    os.chdir(_SERVICE_ROOT)
    result = subprocess.run([_venv_python(), str(_SYNC_SCRIPT)], cwd=str(_SERVICE_ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

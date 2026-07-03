"""One-command cwd-safe launcher for the EKIE API.

Changes to the services/ekie directory before starting uvicorn so that
settings.py can locate the .env file and the --app-dir flag resolves correctly
from any working directory.

Usage:
    python services/ekie/scripts/start_api.py
    # or after pip install -e services/ekie[...]:
    ekie-api
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _SERVICE_ROOT.parents[1]


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


def main() -> int:
    os.chdir(_SERVICE_ROOT)
    port = os.environ.get("EKIE_API_PORT", "8001")
    cmd = [
        _venv_python(),
        "-m",
        "uvicorn",
        "api.app:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--app-dir", "src",
    ]
    result = subprocess.run(cmd, cwd=str(_SERVICE_ROOT))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

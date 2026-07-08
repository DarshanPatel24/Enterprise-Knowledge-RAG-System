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
    # Bootstrap sys.path so the launcher can read the same settings the app uses.
    for path in (_SERVICE_ROOT / "src", _REPO_ROOT / "packages" / "contracts" / "src"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from config.settings import get_settings  # noqa: E402 - after sys.path bootstrap

    settings = get_settings()
    cmd = [
        _venv_python(),
        "-m",
        "uvicorn",
        "api.app:app",
        "--host", settings.gateway.host,
        "--port", str(settings.gateway.port),
        "--app-dir", "src",
    ]
    result = subprocess.run(cmd, cwd=str(_SERVICE_ROOT))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

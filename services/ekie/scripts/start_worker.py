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
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.chdir(_SERVICE_ROOT)


def main() -> None:
    # Import after chdir so settings.py resolves .env correctly.
    from scripts.production_sync import run_worker  # type: ignore[import]
    run_worker()


if __name__ == "__main__":
    main()

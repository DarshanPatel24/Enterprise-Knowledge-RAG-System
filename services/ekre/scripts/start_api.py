"""Start the EKRE FastAPI service with uvicorn."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Bootstrap sys.path so `src/` packages import when run as a script.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

# Co-located .env (services/ekre/.env).
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _load_system_env() -> None:
    """Apply non-``EKRE_`` system variables from the .env into the process.

    Pydantic reads the ``EKRE_`` settings from the same file, but not plain system
    variables such as ``HF_HOME`` / ``HF_HUB_OFFLINE`` that the HuggingFace query
    model needs. Apply them before the model loads, letting real shell values win.
    """
    if not _ENV_FILE.exists():
        return
    for raw_line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("EKRE_") or not key:
            continue
        value = value.strip().strip('"').strip("'")
        # Resolve relative paths (e.g. a shared HF_HOME cache) against the .env
        # directory so they are correct regardless of the launch directory.
        if value.startswith(("./", "../")):
            value = str((_ENV_FILE.parent / value).resolve())
        os.environ.setdefault(key, value)


def main() -> None:
    """Run the EKRE API server."""
    _load_system_env()

    import uvicorn  # noqa: E402 - imported after sys.path + env bootstrap

    from config.settings import get_settings  # noqa: E402

    settings = get_settings()
    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8002,
        log_level=settings.observability.log_level.lower(),
    )


if __name__ == "__main__":
    main()

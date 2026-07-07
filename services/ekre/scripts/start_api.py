"""Start the EKRE FastAPI service with uvicorn."""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path so `src/` packages import when run as a script.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


def main() -> None:
    """Run the EKRE API server."""
    import uvicorn  # noqa: E402 - imported after sys.path bootstrap

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

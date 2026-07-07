"""One-command launcher for the EKIE ingestion job worker pool.

Spawns ``EKIE_INGESTION__WORKER_CONCURRENCY`` worker processes (each a copy of
``production_ingest_worker.py``) and supervises them until interrupted. Run this
alongside the API when ``EKIE_INGESTION__ASYNC_ENABLED=true``.

Usage:
    python services/ekie/scripts/start_ingest_worker.py
    # or after pip install -e services/ekie[...]:
    ekie-ingest-worker
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
_REPO_ROOT = _SERVICE_ROOT.parents[1]
_WORKER_SCRIPT = _SERVICE_ROOT / "scripts" / "production_ingest_worker.py"


def _venv_python() -> str:
    candidates = [
        _REPO_ROOT / ".venv" / "Scripts" / "python.exe",  # Windows
        _REPO_ROOT / ".venv" / "bin" / "python",           # Linux/macOS
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def _worker_concurrency() -> int:
    if str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))
    from config.settings import get_settings

    return max(1, get_settings().ingestion.worker_concurrency)


def main() -> None:
    os.chdir(_SERVICE_ROOT)
    concurrency = _worker_concurrency()
    python = _venv_python()

    processes: list[subprocess.Popen[bytes]] = []
    try:
        for index in range(concurrency):
            worker_id = f"ingest-worker-{os.getpid()}-{index + 1}"
            processes.append(
                subprocess.Popen(
                    [python, str(_WORKER_SCRIPT), "--worker-id", worker_id],
                    cwd=str(_SERVICE_ROOT),
                )
            )
        print(f"[start_ingest_worker] Launched {concurrency} worker process(es). "
              "Press Ctrl+C to stop.")
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\n[start_ingest_worker] Stopping workers...")
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
    sys.exit(0)


if __name__ == "__main__":
    main()

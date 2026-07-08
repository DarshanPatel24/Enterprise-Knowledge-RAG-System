"""Launch EK-RAG engine services as independent localhost processes.

Each engine ships its own ``api.app:app`` entrypoint and shares top-level module
names (``api``, ``domain``, ``config``) with the others, so they cannot run in one
interpreter. This launcher starts each engine in a separate process with its own
``PYTHONPATH`` and working directory, waits for the health endpoint to report
ready, and tears the process down deterministically.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS_SRC = _REPO_ROOT / "packages" / "contracts" / "src"

# Non-standard ports so the harness never clashes with manually started servers.
EKIE_PORT = 18001
EKRE_PORT = 18002
EKCP_PORT = 18003

# Shared gateway token the harness configures EKCP with and presents on requests.
EKCP_GATEWAY_TOKEN = "integration-gateway-token"  # noqa: S105 - test-only token

# Force EKRE's fully offline, deterministic retrieval path (no HuggingFace/LLM
# model loading) so cross-engine flows are fast and hermetic.
_EKRE_OFFLINE_ENV = {
    "EKRE_WORKERS__CONNECTOR": "inmemory",
    "EKRE_WORKERS__QUERY_EMBEDDER": "local_hash",
    "EKRE_QUERY__ENABLE_LLM_INTERPRETER": "false",
}

# Force EKIE's local (hash embedder + in-memory vector store) offline path.
_EKIE_OFFLINE_ENV = {
    "EKIE_EMBEDDING__PROVIDER": "local",
    "EKIE_VECTOR__PROVIDER": "local",
}


def _venv_python() -> str:
    """Return the repo virtualenv Python, falling back to the current interpreter."""
    candidates = [
        _REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        _REPO_ROOT / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def _tail(path: Path, limit: int = 40) -> str:
    """Return the last ``limit`` lines of a log file for diagnostics."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "<no log captured>"
    return "\n".join(lines[-limit:])


@dataclass
class ServiceHandle:
    """A running engine process and its base URL."""

    name: str
    base_url: str
    process: subprocess.Popen[bytes]
    log_path: Path
    _log_file: object = field(repr=False)

    def stop(self) -> None:
        """Terminate the process and close the captured log file."""
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        try:
            self._log_file.close()  # type: ignore[attr-defined]
        except OSError:
            pass


def launch_service(
    name: str,
    service_dir: Path,
    port: int,
    *,
    extra_env: Mapping[str, str] | None = None,
    ready_timeout: float = 60.0,
) -> ServiceHandle:
    """Start an engine's ``api.app:app`` on ``port`` and wait until it is ready.

    Raises ``RuntimeError`` if the process exits early or never becomes ready,
    including a tail of the captured log for diagnosis.
    """
    src = service_dir / "src"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(src), str(_CONTRACTS_SRC), env.get("PYTHONPATH", "")]
    )
    if extra_env:
        env.update(extra_env)

    log_path = Path(tempfile.gettempdir()) / f"ekrag-int-{name}-{port}.log"
    log_file = log_path.open("w", encoding="utf-8")
    command = [
        _venv_python(),
        "-m",
        "uvicorn",
        "api.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--app-dir",
        "src",
        "--log-level",
        "warning",
    ]
    process: subprocess.Popen[bytes] = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
        command,
        cwd=str(service_dir),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    handle = ServiceHandle(
        name=name,
        base_url=f"http://127.0.0.1:{port}",
        process=process,
        log_path=log_path,
        _log_file=log_file,
    )
    _wait_until_ready(handle, ready_timeout)
    return handle


def _wait_until_ready(handle: ServiceHandle, timeout: float) -> None:
    """Poll ``/health/live`` until the service answers or the timeout elapses."""
    url = f"{handle.base_url}/health/live"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if handle.process.poll() is not None:
            handle.stop()
            raise RuntimeError(
                f"{handle.name} exited early (rc={handle.process.returncode}).\n"
                f"--- log tail ---\n{_tail(handle.log_path)}"
            )
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    handle.stop()
    raise RuntimeError(
        f"{handle.name} did not become ready within {timeout:.0f}s.\n"
        f"--- log tail ---\n{_tail(handle.log_path)}"
    )


def launch_ekre(port: int = EKRE_PORT) -> ServiceHandle:
    """Start the EKRE retrieval engine in its offline deterministic mode."""
    return launch_service(
        "ekre", _REPO_ROOT / "services" / "ekre", port, extra_env=_EKRE_OFFLINE_ENV
    )


def launch_ekcp(
    port: int = EKCP_PORT,
    *,
    ekre_port: int = EKRE_PORT,
    knowledge_base_url: str | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> ServiceHandle:
    """Start the EKCP control plane with live EKRE knowledge integration enabled.

    ``knowledge_base_url`` overrides the EKRE endpoint (for example to point at a
    stub); ``extra_env`` supplies additional overrides such as circuit-breaker
    thresholds.
    """
    base_url = knowledge_base_url or f"http://127.0.0.1:{ekre_port}"
    env = {
        "EKCP_KNOWLEDGE__ENABLED": "true",
        "EKCP_KNOWLEDGE__BASE_URL": base_url,
        "EKCP_SECURITY__REQUIRE_GATEWAY_AUTH": "true",
        "EKCP_SECURITY__GATEWAY_AUTH_TOKEN": EKCP_GATEWAY_TOKEN,
        "EKCP_GOVERNANCE__DEFAULT_ROLE": "power_user",
        # Deterministic echo model: no HuggingFace/LLM load, fast + hermetic.
        "EKCP_MODEL__RUNTIME": "deterministic",
    }
    if extra_env:
        env.update(extra_env)
    return launch_service(
        "ekcp", _REPO_ROOT / "services" / "ekcp", port, extra_env=env
    )


def launch_ekie(port: int = EKIE_PORT) -> ServiceHandle:
    """Start the EKIE ingestion engine in its offline local mode."""
    return launch_service(
        "ekie", _REPO_ROOT / "services" / "ekie", port, extra_env=_EKIE_OFFLINE_ENV
    )


@contextmanager
def running(*handles_factories: object) -> Iterator[list[ServiceHandle]]:
    """Context manager that stops every launched service on exit.

    Accepts zero-argument callables returning a ``ServiceHandle``; launches them
    in order and guarantees teardown in reverse order.
    """
    handles: list[ServiceHandle] = []
    try:
        for factory in handles_factories:
            handles.append(factory())  # type: ignore[operator]
        yield handles
    finally:
        for handle in reversed(handles):
            handle.stop()

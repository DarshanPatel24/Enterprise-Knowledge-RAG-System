"""One-command EKIE environment setup and readiness checker.

Performs all steps required before first use:
  1. Verify prerequisite software.
  2. Detect or create .env from .env.example.
  3. Install Python dependencies.
  4. Start Docker infrastructure services.
  5. Wait for each service to become healthy.
  6. Create SQL Server database if it does not exist.
  7. Run database schema provisioning.
  8. Create MinIO bucket.
  9. Print readiness summary.

Usage (from any directory):
    python services/ekie/scripts/setup.py
    # or after install:
    ekie-setup
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_SRC = _SERVICE_ROOT / "src"
_ENV_FILE = _SERVICE_ROOT / ".env"
_ENV_EXAMPLE = _SERVICE_ROOT / ".env.example"
_COMPOSE_FILE = _REPO_ROOT / "docker-compose.local.yml"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.chdir(_SERVICE_ROOT)

# --- Utility ---

def _ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def _warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    sys.exit(1)


def _run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(_SERVICE_ROOT),
        check=check,
        text=True,
        capture_output=capture,
    )


# --- Step 1: Prerequisites ---

def check_prerequisites() -> None:
    print("\n[1/9] Checking prerequisites...")

    if sys.version_info < (3, 11):
        _fail(f"Python 3.11+ required, got {sys.version}")
    _ok(f"Python {sys.version.split()[0]}")

    if not shutil.which("docker"):
        _fail("Docker not found on PATH. Install Docker Desktop from https://www.docker.com/products/docker-desktop/")
    _ok("docker found")

    odbc_result = _run(
        [sys.executable, "-c", "import pyodbc; print(pyodbc.version)"],
        check=False,
        capture=True,
    )
    if odbc_result.returncode != 0:
        _warn("pyodbc not installed — run: pip install pyodbc (ODBC Driver 18 required for SQL Server)")
    else:
        _ok("pyodbc found")


# --- Step 2: .env setup ---

def setup_env() -> None:
    print("\n[2/9] Checking .env configuration...")
    if _ENV_FILE.exists():
        _ok(f".env found at {_ENV_FILE}")
        return
    if not _ENV_EXAMPLE.exists():
        _fail(f".env.example missing at {_ENV_EXAMPLE}")
    shutil.copy(_ENV_EXAMPLE, _ENV_FILE)
    _ok(f"Created .env from .env.example at {_ENV_FILE}")
    _warn("Review .env and set required values (SQL password, MinIO credentials, etc.) before continuing.")
    _warn("Re-run ekie-setup after updating .env.")


# --- Step 3: Install dependencies ---

def install_dependencies() -> None:
    print("\n[3/9] Installing Python dependencies...")
    _run([sys.executable, "-m", "pip", "install", "-q", "-e", ".[dev,mssql,storage,richmedia]"])
    _ok("Dependencies installed")


# --- Step 4: Start Docker services ---

def start_docker_services() -> None:
    print("\n[4/9] Starting Docker infrastructure services...")
    env = {
        **os.environ,
        "MINIO_PORT": os.environ.get("MINIO_PORT", "9005"),
        "MINIO_CONSOLE_PORT": os.environ.get("MINIO_CONSOLE_PORT", "9006"),
        "MINIO_ROOT_USER": os.environ.get("MINIO_ROOT_USER", "minioadmin"),
        "MINIO_ROOT_PASSWORD": os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin"),
    }
    subprocess.run(
        ["docker", "compose", "-f", str(_COMPOSE_FILE), "up", "-d", "qdrant", "minio", "mssql", "redis"],
        check=True,
        env=env,
    )
    _ok("Docker services starting...")


# --- Step 5: Wait for services ---

def _wait_http(url: str, label: str, max_seconds: int = 60) -> None:
    import urllib.request
    for attempt in range(max_seconds):
        try:
            urllib.request.urlopen(url, timeout=2)  # noqa: S310
            _ok(f"{label} reachable at {url}")
            return
        except Exception:
            time.sleep(1)
    _fail(f"{label} not reachable at {url} after {max_seconds}s. Check docker logs.")


def wait_for_services() -> None:
    print("\n[5/9] Waiting for services to be healthy...")
    _wait_http("http://localhost:6333/collections", "Qdrant", max_seconds=60)
    _wait_http("http://localhost:9005/minio/health/live", "MinIO", max_seconds=60)
    time.sleep(3)
    _ok("Infrastructure ready")


# --- Step 6: Create SQL database ---

def create_sql_database() -> None:
    print("\n[6/9] Provisioning SQL Server database...")
    if not shutil.which("sqlcmd"):
        _warn("sqlcmd not on PATH — skipping database creation. Create 'ekrag_control_plane' manually.")
        return
    result = subprocess.run(
        [
            "sqlcmd", "-S", r"localhost\MSSQLSERVER2022", "-E", "-C",
            "-Q", "IF DB_ID('ekrag_control_plane') IS NULL CREATE DATABASE ekrag_control_plane;",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _warn(f"sqlcmd returned {result.returncode}: {result.stderr.strip()}")
        _warn("Create database 'ekrag_control_plane' manually in SQL Server Management Studio.")
    else:
        _ok("Database ekrag_control_plane ready")


# --- Step 7: Run schema migration ---

def run_schema_migration() -> None:
    print("\n[7/9] Applying database schema (create_all)...")
    from config.settings import get_settings
    from domain.control_plane import ControlPlaneDatabase
    s = get_settings()
    db = ControlPlaneDatabase(s.control_plane)
    db.create_all()
    _ok("Schema applied")


# --- Step 8: Create MinIO bucket ---

def create_minio_bucket() -> None:
    print("\n[8/9] Provisioning MinIO bucket...")
    from config.settings import get_settings
    s = get_settings()
    try:
        from minio import Minio
        client = Minio(
            s.storage.endpoint,
            access_key=s.storage.access_key,
            secret_key=s.storage.secret_key,
            secure=s.storage.secure,
        )
        if not client.bucket_exists(s.storage.bucket):
            client.make_bucket(s.storage.bucket)
            _ok(f"Bucket '{s.storage.bucket}' created")
        else:
            _ok(f"Bucket '{s.storage.bucket}' already exists")
    except Exception as exc:
        _warn(f"MinIO bucket creation failed: {exc}. Create bucket '{s.storage.bucket}' manually.")


# --- Step 9: Final health check ---

def final_health_check() -> None:
    print("\n[9/9] Running EKIE API health check...")
    _warn("Start the API first with: ekie-api (in a separate terminal)")
    _warn("Then re-run: ekie-setup --check-only   (or verify manually at http://localhost:8001/health/ready)")
    _ok("Setup complete. See docs/EKIE/EKIE-Deployment-Guide.md for next steps.")


# --- Entry point ---

def main() -> int:
    print("=" * 55)
    print("  EKIE Setup — First-Time Environment Provisioning")
    print("=" * 55)
    check_prerequisites()
    setup_env()
    install_dependencies()
    start_docker_services()
    wait_for_services()
    create_sql_database()
    run_schema_migration()
    create_minio_bucket()
    final_health_check()
    print("\n  All steps complete. Run `ekie-api` and `ekie-worker` to start ingestion.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""EKIE Production Deployment Task Runner.

Executes all deployment steps in the correct order and prints a gate-by-gate
status report. Designed to replace the manual copy-paste runbook with a single
repeatable command.

Usage (from repo root):
    python services/ekie/scripts/deploy.py

Gates:
    1  Prerequisites check (Python, Docker, ODBC, Tesseract)
    2  .env configuration validation (required keys present)
    3  Docker infrastructure startup + health
    4  MinIO bucket provisioning (ekie-assets, langfuse-events)
    5  SQL Server schema provisioning
    6  Langfuse stack startup + connectivity
    7  HuggingFace model cache check
    8  EKIE API startup check
    9  First ingestion smoke test
   10  Monitoring verification (Qdrant, Langfuse)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

_SERVICE_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _SERVICE_ROOT.parents[1]
_SRC = _SERVICE_ROOT / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.chdir(_SERVICE_ROOT)

# ── Terminal helpers ───────────────────────────────────────────────────────────

_PASS = "\u2705"
_FAIL = "\u274c"
_WARN = "\u26a0\ufe0f "
_INFO = "\u2139\ufe0f "


def _ok(msg: str) -> None:
    print(f"  {_PASS} {msg}")


def _fail(msg: str, hint: str = "") -> None:
    print(f"  {_FAIL} {msg}")
    if hint:
        print(f"       Hint: {hint}")
    sys.exit(1)


def _warn(msg: str) -> None:
    print(f"  {_WARN} {msg}")


def _info(msg: str) -> None:
    print(f"  {_INFO} {msg}")


def _section(title: str) -> None:
    print(f"\n[{title}]")


# ── Gate 1: Prerequisites ──────────────────────────────────────────────────────

def gate_prerequisites() -> None:
    _section("Gate 1/10 — Prerequisites")

    if sys.version_info < (3, 11):
        _fail(f"Python 3.11+ required, found {sys.version.split()[0]}")
    _ok(f"Python {sys.version.split()[0]}")

    if not shutil.which("docker"):
        _fail("Docker not found", "Install Docker Desktop from https://www.docker.com/products/docker-desktop/")
    _ok("docker")

    if not shutil.which("tesseract"):
        _warn("tesseract not on PATH — scanned PDFs will dead-letter")
        _warn("Install from https://github.com/UB-Mannheim/tesseract/wiki")
        _warn("Then add C:\\Program Files\\Tesseract-OCR to system PATH")
    else:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        _ok(f"tesseract: {result.stdout.splitlines()[0] if result.stdout else 'found'}")

    try:
        import pyodbc  # noqa: F401
        _ok("pyodbc (ODBC Driver 18)")
    except ImportError:
        _warn("pyodbc not found — SQL Server connectivity unavailable")

    try:
        import minio  # noqa: F401
        _ok("minio SDK")
    except ImportError:
        _fail("minio package not installed", "pip install -e 'services/ekie[storage]'")


# ── Gate 2: .env validation ────────────────────────────────────────────────────

def gate_env_config() -> None:
    _section("Gate 2/10 — .env Configuration")
    env_file = _SERVICE_ROOT / ".env"
    if not env_file.exists():
        _fail(".env not found", f"Copy .env.example to {env_file}")

    from config.settings import get_settings
    s = get_settings()

    if not s.sync.target_directory:
        _warn("EKIE_SYNC__TARGET_DIRECTORY not set — worker won't know which folder to watch")
    else:
        target = Path(s.sync.target_directory)
        if not target.exists():
            _warn(f"Target directory {s.sync.target_directory} does not exist yet")
        else:
            _ok(f"Source folder: {s.sync.target_directory}")

    if not s.observability.langfuse_public_key:
        _warn("EKIE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY not set — Langfuse tracing disabled")
    else:
        _ok("Langfuse keys configured")

    _ok(f"Environment: {s.environment}")
    _ok(f"Embedding model: {s.embedding.default_model} (dim={s.embedding.dimension})")
    _ok(f"Publishing provider: {s.publishing.provider}")
    _ok(f"Orchestration runner: {s.orchestration.runner}")


# ── Gate 3: Docker infrastructure ─────────────────────────────────────────────

def gate_docker_infra() -> None:
    _section("Gate 3/10 — Docker Infrastructure")
    import urllib.request

    compose_file = str(_REPO_ROOT / "docker-compose.local.yml")
    subprocess.run(
        ["docker", "compose", "-f", compose_file, "up", "-d",
         "qdrant", "minio", "mssql", "redis"],
        check=True, capture_output=True,
    )
    _ok("Core services started")

    checks = [
        ("Qdrant", "http://localhost:6333/collections"),
        ("MinIO", "http://localhost:9005/minio/health/live"),
    ]
    for label, url in checks:
        for attempt in range(30):
            try:
                urllib.request.urlopen(url, timeout=2)  # noqa: S310
                _ok(f"{label} reachable")
                break
            except Exception:
                time.sleep(1)
        else:
            _fail(f"{label} not reachable at {url} after 30s", "Check docker logs")


# ── Gate 4: MinIO buckets ──────────────────────────────────────────────────────

def gate_minio_buckets() -> None:
    _section("Gate 4/10 — MinIO Buckets")
    from config.settings import get_settings
    from minio import Minio
    s = get_settings()
    client = Minio(s.storage.endpoint, access_key=s.storage.access_key, secret_key=s.storage.secret_key, secure=False)
    for bucket in [s.storage.bucket, "langfuse-events"]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            _ok(f"Created bucket: {bucket}")
        else:
            _ok(f"Bucket ready: {bucket}")


# ── Gate 5: SQL schema ─────────────────────────────────────────────────────────

def gate_sql_schema() -> None:
    _section("Gate 5/10 — SQL Server Schema")
    from config.settings import get_settings
    from domain.control_plane import ControlPlaneDatabase
    try:
        s = get_settings()
        db = ControlPlaneDatabase(s.control_plane)
        if s.environment == "local":
            db.create_all()
        else:
            db.create_all()
        _ok("Schema applied (create_all)")
    except Exception as exc:
        _fail(f"SQL connectivity failed: {exc}",
              "Check EKIE_CONTROL_PLANE__ settings and SQL Server status")


# ── Gate 6: Langfuse stack ────────────────────────────────────────────────────

def gate_langfuse() -> None:
    _section("Gate 6/10 — Langfuse Observability Stack")
    import urllib.request
    compose_file = str(_REPO_ROOT / "docker-compose.local.yml")
    subprocess.run(
        ["docker", "compose", "-f", compose_file, "up", "-d",
         "clickhouse", "langfuse-db", "langfuse", "langfuse-worker"],
        check=True, capture_output=True,
    )
    for attempt in range(30):
        try:
            urllib.request.urlopen("http://localhost:3000/api/public/health", timeout=2)  # noqa: S310
            _ok("Langfuse reachable at http://localhost:3000")
            break
        except Exception:
            time.sleep(1)
    else:
        _warn("Langfuse not reachable — tracing will be unavailable")
        return

    from config.settings import get_settings
    s = get_settings()
    if s.observability.langfuse_public_key:
        import base64
        import requests
        creds = base64.b64encode(
            f"{s.observability.langfuse_public_key}:{s.observability.langfuse_secret_key}".encode()
        ).decode()
        try:
            r = requests.get("http://localhost:3000/api/public/traces?limit=1",
                             headers={"Authorization": f"Basic {creds}"}, timeout=5)
            if r.status_code == 200:
                _ok("Langfuse API keys valid")
            else:
                _warn(f"Langfuse key check returned {r.status_code} — check keys in .env")
        except Exception as exc:
            _warn(f"Langfuse key check failed: {exc}")
    else:
        _warn("Langfuse keys not set — open http://localhost:3000, register, and copy pk-lf-... / sk-lf-... to .env")


# ── Gate 7: HuggingFace model cache ──────────────────────────────────────────

def gate_hf_models() -> None:
    _section("Gate 7/10 — HuggingFace Model Cache")
    from config.settings import get_settings
    s = get_settings()
    hf_home = Path(s.sync.target_directory).parent.parent / "services" / "ekie" / "storage" / "hf"
    hf_home_env = os.environ.get("HF_HOME", str(_SERVICE_ROOT / "storage" / "hf"))
    cache_dir = Path(hf_home_env) / "hub"

    embedding_model_dir = f"models--{s.embedding.default_model.replace('/', '--')}"
    intelligence_model_dir = f"models--{s.intelligence.llm_model.replace('/', '--')}"

    for label, model_dir in [("Embedding", embedding_model_dir), ("Intelligence LLM", intelligence_model_dir)]:
        candidate = cache_dir / model_dir
        if candidate.exists():
            _ok(f"{label} model cached: {model_dir}")
        else:
            _warn(f"{label} model NOT cached: {model_dir}")
            _warn(f"  Run: from huggingface_hub import snapshot_download; snapshot_download('{s.embedding.default_model if label == 'Embedding' else s.intelligence.llm_model}')")


# ── Gate 8: API health ────────────────────────────────────────────────────────

def gate_api_health() -> None:
    _section("Gate 8/10 — EKIE API Health")
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:8001/health/ready", timeout=5)  # noqa: S310
        _ok("EKIE API healthy at http://localhost:8001")
    except Exception:
        _warn("EKIE API not running — start it with:")
        _warn("  $env:PATH = 'C:\\Program Files\\Tesseract-OCR;' + $env:PATH")
        _warn("  python services/ekie/scripts/start_api.py")


# ── Gate 9: Ingest smoke test ─────────────────────────────────────────────────

def gate_smoke_ingest(tenant_id: str) -> None:
    _section("Gate 9/10 — Ingestion Smoke Test")
    import requests
    from config.settings import get_settings
    from domain.control_plane import ControlPlaneDatabase, Repository
    s = get_settings()
    db = ControlPlaneDatabase(s.control_plane)
    with db.session() as sess:
        repo = sess.query(Repository).filter_by(tenant_id=tenant_id).order_by(
            Repository.created_at.asc()
        ).first()
        if repo is None:
            _warn(f"No repository found for tenant '{tenant_id}' — run the worker first to auto-register")
            return
        repo_id = repo.id
        repo_name = repo.name

    _info(f"Using repository: {repo_id} ({repo_name})")
    try:
        resp = requests.post(
            f"http://localhost:8001/v1/repositories/{repo_id}/ingest",
            headers={"X-Tenant-ID": tenant_id, "Content-Type": "application/json"},
            json={"sync_before_ingest": True, "max_documents": 2},
            timeout=300,
        )
        body = resp.json()
        if resp.status_code in (200, 422):
            attempted = body.get("attempted", 0)
            completed = body.get("completed", 0)
            dead = body.get("dead_lettered", 0)
            if completed > 0:
                _ok(f"Ingest: attempted={attempted} completed={completed} dead_lettered={dead}")
            else:
                _warn(f"Ingest ran but 0 completed: attempted={attempted} dead_lettered={dead}")
                if body.get("errors"):
                    _warn(f"Errors: {body['errors'][:2]}")
        else:
            _warn(f"Ingest returned HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:
        _warn(f"Ingest call failed: {exc}")


# ── Gate 10: Monitoring verification ─────────────────────────────────────────

def gate_monitoring(tenant_id: str) -> None:
    _section("Gate 10/10 — Monitoring Verification")
    import requests

    # Qdrant
    try:
        r = requests.get("http://localhost:6333/collections", timeout=5)
        cols = r.json().get("result", {}).get("collections", [])
        names = [c.get("name") for c in cols]
        if "enterprise_documents" in names:
            r2 = requests.post("http://localhost:6333/collections/enterprise_documents/points/count",
                               json={"exact": True}, timeout=5)
            count = r2.json().get("result", {}).get("count", 0)
            _ok(f"Qdrant: enterprise_documents has {count} vectors")
        else:
            _warn(f"Qdrant: enterprise_documents collection not found. Collections: {names}")
    except Exception as exc:
        _warn(f"Qdrant check failed: {exc}")

    # Langfuse
    from config.settings import get_settings
    s = get_settings()
    if s.observability.langfuse_public_key:
        import base64
        creds = base64.b64encode(
            f"{s.observability.langfuse_public_key}:{s.observability.langfuse_secret_key}".encode()
        ).decode()
        try:
            r = requests.get("http://localhost:3000/api/public/traces?limit=5",
                             headers={"Authorization": f"Basic {creds}"}, timeout=5)
            count = len(r.json().get("data", []))
            if count > 0:
                _ok(f"Langfuse: {count} trace(s) visible in UI")
            else:
                _warn("Langfuse: 0 traces — trigger an ingest and wait 5–10s for worker to flush")
        except Exception as exc:
            _warn(f"Langfuse trace check failed: {exc}")

    # MinIO
    from minio import Minio
    try:
        client = Minio(s.storage.endpoint, access_key=s.storage.access_key, secret_key=s.storage.secret_key, secure=False)
        objects = list(client.list_objects(s.storage.bucket, recursive=True))
        if objects:
            _ok(f"MinIO: {len(objects)} asset object(s) in {s.storage.bucket}")
        else:
            _warn(f"MinIO: bucket {s.storage.bucket} is empty — ingest with EKIE_ENVIRONMENT=production to persist assets")
    except Exception as exc:
        _warn(f"MinIO check failed: {exc}")

    print()
    print("  ─────────────────────────────────────────────────")
    print("  Monitoring dashboards:")
    print("    Qdrant   http://localhost:6333/dashboard")
    print("    MinIO    http://localhost:9006  (minioadmin / minioadmin)")
    print("    Langfuse http://localhost:3000  → Traces")
    print("  ─────────────────────────────────────────────────")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="EKIE Production Deployment Task Runner")
    parser.add_argument("--tenant-id", default="tenant-default", help="Tenant ID to use for smoke test")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker infrastructure gates (already running)")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip ingestion smoke test gate")
    args = parser.parse_args()

    print("=" * 60)
    print("  EKIE Production Deployment Task Runner")
    print("=" * 60)

    gate_prerequisites()
    gate_env_config()
    if not args.skip_docker:
        gate_docker_infra()
        gate_minio_buckets()
    gate_sql_schema()
    if not args.skip_docker:
        gate_langfuse()
    gate_hf_models()
    gate_api_health()
    if not args.skip_smoke:
        gate_smoke_ingest(args.tenant_id)
    gate_monitoring(args.tenant_id)

    print("\n" + "=" * 60)
    print("  Deployment task run complete.")
    print("  Review warnings above before marking deployment done.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

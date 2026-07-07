# EKIE Deployment Guide

**Audience:** Engineers, DevOps, and platform operators.  
**Last updated:** 2026-07-03

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Docker Infrastructure Setup](#2-docker-infrastructure-setup)
3. [Python Environment Setup](#3-python-environment-setup)
4. [Configuration Reference (.env)](#4-configuration-reference)
5. [First-Time Schema Provisioning](#5-first-time-schema-provisioning)
6. [Starting Services](#6-starting-services)
7. [Ingestion Verification Checklist](#7-ingestion-verification-checklist)
8. [Production Hardening](#8-production-hardening)
9. [Pre-Production Cleanup](#9-pre-production-cleanup)
10. [Upgrade and Rollback](#10-upgrade-and-rollback)
11. [Known Gaps and Roadmap](#11-known-gaps-and-roadmap)

---

## 1. Prerequisites

### 1.1 Software Requirements

| Software | Version | Installation |
|---|---|---|
| Python | 3.11+ | https://www.python.org/downloads/ |
| Docker Desktop | Latest stable | https://www.docker.com/products/docker-desktop/ |
| ODBC Driver 18 for SQL Server | Latest | https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server |
| Git | Latest | https://git-scm.com/ |
| sqlcmd (SQL Server tools) | Latest | Bundled with SSMS or downloadable separately |

### 1.2 Optional Software

| Software | When needed |
|---|---|
| Ollama | When `EKIE_EMBEDDING__PROVIDER=ollama` or `EKIE_INTELLIGENCE__LLM_PROVIDER=ollama` |
| NVIDIA GPU + CUDA | When using large HuggingFace models locally |

> EKIE ingests Markdown only. Converting other formats (PDF, DOCX, PPTX, HTML,
> CSV, images, audio, video) to Markdown is handled upstream by the EKDC agent
> (`services/ekdc`), so no OCR/rich-media libraries are required by EKIE.

### 1.3 Hardware Minimums

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32 GB (with local HF models) |
| Disk | 40 GB free | 100 GB SSD |
| GPU | Not required | NVIDIA GPU accelerates HF model inference |

### 1.4 Network

All services run locally. No outbound internet access is required in production except:
- First-time HuggingFace model download (cache once, then set `HF_HUB_OFFLINE=1`)
- Docker image pulls on first `docker compose up`

---

## 2. Docker Infrastructure Setup

### 2.1 Environment Variables for Docker

Create a root-level `.env` file at the repository root OR set shell variables before running compose:

```powershell
$env:MINIO_ROOT_USER = "minioadmin"
$env:MINIO_ROOT_PASSWORD = "minioadmin"
$env:MINIO_PORT = "9005"
$env:MINIO_CONSOLE_PORT = "9006"
# SQL Server is the Windows-native instance (not Docker) — no SA password needed here
$env:LANGFUSE_DB_USER = "langfuse"
$env:LANGFUSE_DB_PASSWORD = "langfuse"
$env:LANGFUSE_NEXTAUTH_SECRET = "change-in-production"
$env:LANGFUSE_SALT = "change-in-production"
```

> **SQL Server:** EKIE uses your Windows-native SQL Server instance (`localhost\MSSQLSERVER2022`) via Windows Authentication. There is **no Docker MSSQL container** in this stack.

### 2.2 Start Core Infrastructure

```powershell
docker compose -f docker-compose.local.yml up -d qdrant minio redis
```

Wait for healthy status:

```powershell
docker compose -f docker-compose.local.yml ps
# qdrant, minio, and redis should show (healthy) before proceeding.
```

### 2.3 Create MinIO Bucket

After MinIO starts, create the asset bucket:

```powershell
# Using the Python SDK (after dependencies are installed):
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -c "
from minio import Minio
c = Minio('localhost:9005', access_key='minioadmin', secret_key='minioadmin', secure=False)
if not c.bucket_exists('ekie-assets'):
    c.make_bucket('ekie-assets')
    print('bucket created')
else:
    print('bucket already exists')
"
Pop-Location
```

Or use the MinIO Console at http://localhost:9006 (login: minioadmin / minioadmin).

### 2.4 Create SQL Server Database

EKIE connects to your Windows-native SQL Server instance via Windows Authentication. Create the database once:

```powershell
sqlcmd -S "localhost\MSSQLSERVER2022" -E -C -Q "IF DB_ID('ekrag_control_plane') IS NULL CREATE DATABASE ekrag_control_plane;"
```

> There is no Docker MSSQL container. If you receive a connection error, verify the `MSSQL$MSSQLSERVER2022` Windows service is running: `Get-Service MSSQL\$MSSQLSERVER2022`

### 2.5 Start Langfuse Observability Stack

Langfuse 3.x requires **two containers**: the web app and a worker. Both must run for ingestion events to appear in the UI.

```powershell
docker compose -f docker-compose.local.yml up -d clickhouse langfuse-db langfuse langfuse-worker
docker compose -f docker-compose.local.yml ps clickhouse langfuse-db langfuse langfuse-worker
# All four should show (healthy) or Up.
```

The `langfuse-worker` container processes queued ingestion events and writes them to ClickHouse. Without it, all traces are accepted with HTTP 207 but never appear in the Langfuse UI.

After both containers are healthy, log in at http://localhost:3000, create your account, create a project, and copy the API keys to `.env`:

```dotenv
EKIE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY=pk-lf-...
EKIE_OBSERVABILITY__LANGFUSE_SECRET_KEY=sk-lf-...
```

---

## 3. Python Environment Setup

### 3.1 Create and Activate Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3.2 Install Dependencies

```powershell
# Core service + all production extras including VL embedding model support
pip install -e "services/ekie[dev,mssql,storage]"
pip install -e packages/contracts

# Required for Qwen3-VL-Embedding-2B (vision-language embedding model)
pip install -U "sentence-transformers[image]" torchvision

# Required for HuggingFace intelligence LLM (Qwen/Qwen2.5-7B-Instruct)
pip install langchain-huggingface torch transformers accelerate

# GPU acceleration (NVIDIA): the default `torch` above is CPU-only. Install a CUDA
# build matching your driver INSTEAD, e.g. for a CUDA 13 driver:
pip install --force-reinstall "torch==2.12.1" --index-url https://download.pytorch.org/whl/cu130
#   (use .../whl/cu128 or cu126 for older drivers). Verify with:
#   python -c "import torch; print(torch.cuda.is_available())"
# Then in services/ekie/.env set EKIE_EMBEDDING__DEVICE=auto and
# EKIE_EMBEDDING__TORCH_DTYPE=float16 (float16 halves VRAM so a 2B model uses
# ~4.3GB and fits a 6GB GPU; fp32 would need ~8GB and OOM).

# Required for Langfuse tracing
pip install "langfuse>=2.0,<3.0"

# Optional: Ollama embedding / intelligence
pip install langchain-ollama
```

> **Document conversion is handled by EKDC, not EKIE.** Point
> `EKIE_SYNC__TARGET_DIRECTORY` at the EKDC `OUTPUT_DIRECTORY` (Markdown files);
> EKIE ingests those `.md` files directly. No Tesseract/OCR install is needed.

### 3.3 Automated One-Command Setup

Two automation levels are available:

#### Option A — `deploy.py` (recommended for new deployments)

The deployment task runner executes all 10 gates in order and reports pass/fail per gate:

```powershell
# From any directory:
python services/ekie/scripts/deploy.py

# Or after pip install -e services/ekie[...]:
ekie-deploy
```

What it does automatically:
1. Prerequisite check (Python, Docker, pyodbc)
2. `.env` validation (required keys present, target folder exists)
3. Docker infrastructure startup (Qdrant, MinIO, Redis)
4. MinIO bucket provisioning (`ekie-assets`, `langfuse-events`)
5. SQL Server schema provisioning (`create_all`)
6. Langfuse stack startup + key validation
7. HuggingFace model cache check
8. EKIE API health check
9. Ingestion smoke test (max 2 documents)
10. Monitoring verification (Qdrant count, Langfuse traces, MinIO objects)

Flags:
```powershell
# Skip Docker startup (already running):
python services/ekie/scripts/deploy.py --skip-docker

# Use a different tenant:
python services/ekie/scripts/deploy.py --tenant-id my-tenant

# Skip ingestion smoke test:
python services/ekie/scripts/deploy.py --skip-smoke
```

All gates must show `[OK]` or `[WARN]` before marking a deployment done. Any `[FAIL]` stops execution with a remediation hint.

#### Option B — `setup.py` (infrastructure-only, first-time)

The setup script performs infrastructure steps 2–5 only (no ingestion smoke test, no monitoring check):

```powershell
python services/ekie/scripts/setup.py
# or after install:
ekie-setup
```

---

## 4. Configuration Reference

### 4.1 Copy Template

```powershell
Copy-Item services/ekie/.env.example services/ekie/.env
```

### 4.2 Minimum Required Values

These keys have no safe default and **must** be set before starting EKIE:

| Key | Purpose | Example |
|---|---|---|
| `EKIE_CONTROL_PLANE__HOST` | SQL Server host/instance | `localhost\MSSQLSERVER2022` |
| `EKIE_CONTROL_PLANE__TRUSTED_CONNECTION` | Windows auth | `true` |
| `EKIE_SYNC__TARGET_DIRECTORY` | Folder of EKDC-generated Markdown to ingest | `D:\Enterprise\Markdown` |
| `EKIE_SYNC__TENANT_ID` | Default tenant identifier | `tenant-prod` |

### 4.3 Storage Configuration (Assets)

EKIE persists every stage payload (canonical Markdown, chunk sets, embeddings,
published-vector manifests) in an immutable, versioned asset store. Two backends
are available:

| Backend | When used | Persistence |
|---|---|---|
| **Local filesystem** (`LocalFileAssetStorage`) | Default local-first path (`EKIE_ENVIRONMENT=local`) | On disk under `EKIE_STORAGE__LOCAL_PATH`; survives API/worker restarts |
| **MinIO** (`MinIOAssetStorage`) | `EKIE_ENVIRONMENT` is not `local` **and** `EKIE_STORAGE__ENDPOINT` is set | Object store; survives restarts |

| Key | Default | Notes |
|---|---|---|
| `EKIE_STORAGE__LOCAL_PATH` | `storage/assets` | Persistent asset directory (relative to the service working dir) used in local mode |
| `EKIE_STORAGE__ENDPOINT` | `localhost:9000` | MinIO endpoint; used only outside local mode |
| `EKIE_STORAGE__ACCESS_KEY` | `` | MinIO access key |
| `EKIE_STORAGE__SECRET_KEY` | `` | MinIO secret key |
| `EKIE_STORAGE__BUCKET` | `ekie-assets` | MinIO bucket |
| `EKIE_ENVIRONMENT` | `local` | `local` selects the filesystem backend; any other value with an endpoint selects MinIO |

**Critical:** In local mode, assets are written to disk (`storage/assets`) and
**survive restarts** — a resumed ingestion job re-reads completed-stage payloads
instead of failing. (Earlier builds used an in-memory backend in local mode,
which lost all payloads on restart and caused resumed jobs to dead-letter with
`markdown payload unavailable`; see
[Help Guide 19.1](EKIE-Help_Guide.md#191-common-issues).) The `storage/`
directory is git-ignored. Back it up alongside the Control Plane database if you
need to preserve in-flight ingestion state across machine moves.

### 4.4 Embedding Configuration

| Key | Current value | Notes |
|---|---|---|
| `EKIE_EMBEDDING__PROVIDER` | `huggingface` | `local` = hash-based (CI/offline), `huggingface` for real embeddings |
| `EKIE_EMBEDDING__DEFAULT_MODEL` | `Qwen/Qwen3-VL-Embedding-2B` | Vision-language embedding model; 2B parameter variant |
| `EKIE_EMBEDDING__DIMENSION` | `1536` | Output dimension for Qwen3-VL-Embedding-2B |
| `EKIE_EMBEDDING__BATCH_SIZE` | `16` | Chunks per embedding request; raise (32-64) for throughput |
| `EKIE_EMBEDDING__MAX_REQUESTS_PER_MINUTE` | `0` | Optional cap on embedding requests/min (0 = unlimited) |
| `HF_HOME` | `./storage` | Local cache path for downloaded model weights |

**Prerequisites for Qwen3-VL-Embedding-2B:**

This model is part of the Qwen3 vision-language family and requires additional image processing libraries:

```powershell
pip install -U "sentence-transformers[image]" torchvision
```

First-run behavior:
1. On first ingest request, model weights (~4 GB) are downloaded to `HF_HOME`.
2. All subsequent requests load weights from local cache — no internet required.
3. To force offline-only after download: add `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` to `.env`.

**Dimension reference for other Qwen3 embedding models:**

| Model | Dimension |
|---|---|
| `Qwen/Qwen3-VL-Embedding-2B` | 1536 |
| `Qwen/Qwen3-VL-Embedding-8B` | 3584 |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 |
| `nomic-embed-text` (Ollama) | 768 |

**Warning:** Changing the embedding model after data is already ingested requires re-ingesting all documents because Qdrant collection dimensions cannot change in place.

**Optional ingestion tuning (all off/opt-in by default):**

| Key | Default | Purpose |
|---|---|---|
| `EKIE_CHUNKING__DEFAULT_STRATEGY=recursive` | `semantic` | Use LangChain recursive character chunking (opt-in). Requires `pip install langchain-text-splitters` |
| `EKIE_CHUNKING__RECURSIVE_CHUNK_SIZE` / `_OVERLAP` | `1000` / `200` | Recursive window and overlap (overlap < size) |
| `EKIE_PUBLISHING__BATCH_SIZE` | `64` | Vectors per Qdrant upsert; raise (128-256) for faster ingest |
| `EKIE_PUBLISHING__MAX_VECTORS_PER_MINUTE` | `0` | Optional cap on vectors upserted/min (0 = unlimited) |
| `EKIE_QDRANT__URL` / `EKIE_QDRANT__API_KEY` | *(empty)* | Optional full URL/API key for the LangChain index template |

The **LangChain index template** (`build_langchain_index`) reads `EKIE_EMBEDDING__*` and `EKIE_QDRANT__*` to return a ready embedding model + Qdrant vector store; requires `pip install langchain-qdrant`. It is a convenience/index seam and does not change the verified publishing path.

### 4.5 Langfuse Observability

Langfuse is enabled in the current configuration. Every ingestion workflow emits a trace visible in the Langfuse UI at http://localhost:3000.

Required `.env` settings (already active):

```dotenv
EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true
EKIE_OBSERVABILITY__LANGFUSE_HOST=http://localhost:3000
EKIE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY=pk-lf-<your-key>
EKIE_OBSERVABILITY__LANGFUSE_SECRET_KEY=sk-lf-<your-key>
EKIE_ORCHESTRATION__RUNNER=langgraph
EKIE_ORCHESTRATION__ENABLE_TRACING=true
```

**How to get API keys:**
1. Start the full Langfuse stack (Section 2.5).
2. Open http://localhost:3000 and register an account.
3. Create an organization and project.
4. Go to Settings → API Keys → Create new key pair.
5. Paste `pk-lf-...` and `sk-lf-...` into `.env`.
6. Restart the EKIE API after setting keys.

**Verify ingestion traces appear:**

```powershell
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -c "
import sys, requests, base64; sys.path.insert(0, 'src')
from config.settings import get_settings; s = get_settings()
creds = base64.b64encode(f'{s.observability.langfuse_public_key}:{s.observability.langfuse_secret_key}'.encode()).decode()
resp = requests.get('http://localhost:3000/api/public/traces?limit=5', headers={'Authorization': f'Basic {creds}'})
print('Traces:', len(resp.json().get('data', [])))
"
Pop-Location
```

**Langfuse Python SDK version:** pin to `langfuse>=2.0,<3.0`. Version 4.x switched to OpenTelemetry protocol which is incompatible with the self-hosted stack.

Start the Langfuse stack before the EKIE API:

```powershell
docker compose -f docker-compose.local.yml up -d clickhouse langfuse-db langfuse
docker compose -f docker-compose.local.yml ps clickhouse langfuse-db langfuse
```

Verify Langfuse is reachable:

```powershell
Invoke-RestMethod http://localhost:3000/api/public/health
# Expected: { "status": "OK" }
```

If Langfuse fails to start, see [Section 19 — Troubleshooting Langfuse](EKIE-Help_Guide.md#217-langfuse-monitoring-path) in the help guide.

### 4.6 Document Intelligence (LLM Analysis)

LLM-based topic extraction and summarization is enabled and uses `Qwen/Qwen2.5-7B-Instruct` locally.

Required `.env` settings (already active):

```dotenv
EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS=true
EKIE_INTELLIGENCE__LLM_PROVIDER=huggingface
EKIE_INTELLIGENCE__LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

Prerequisites:

```powershell
pip install langchain-huggingface torch transformers accelerate
```

First-run behavior: model weights (~15 GB) are downloaded to `HF_HOME` on first document with high complexity. All subsequent inference is local.

To disable temporarily (for performance testing):

```dotenv
EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS=false
```

### 4.7 Environment Profiles

Pre-built configuration profiles for common deployment scenarios:

| Profile file | Scenario |
|---|---|
| `.env.profile.ollama` | Ollama-first: all models via local Ollama server |
| `.env.profile.huggingface` | HuggingFace-first: models downloaded locally |
| `.env.profile.hybrid` | LLM via HF, embeddings via Ollama |
| `.env.profile.rollback-last-known-good` | Minimal validated config for recovery |

Apply a profile:

```powershell
Copy-Item services/ekie/.env.profile.ollama services/ekie/.env -Force
```

---

## 5. First-Time Schema Provisioning

Run from `services/ekie/` (or from repo root using the entry point):

```powershell
# From services/ekie/:
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -c "
from config.settings import get_settings
from domain.control_plane import ControlPlaneDatabase
db = ControlPlaneDatabase(get_settings().control_plane)
db.create_all()
print('Schema applied')
"
Pop-Location

# Or using the setup script (does everything):
python services/ekie/scripts/setup.py
```

**Note:** `create_all()` is safe to re-run; it creates missing tables and leaves existing data intact.

---

## 6. Starting Services

EKIE runs as a small set of cooperating processes. A typical local session uses
these terminals:

| Terminal | Process | Required | Purpose |
|---|---|---|---|
| A | `start_api.py` (`ekie-api`) | Yes | REST API / ingestion endpoints |
| B | `start_worker.py` (`ekie-worker`) | Yes | Watches the target folder and submits documents for ingestion |
| B2 | `start_ingest_worker.py` (`ekie-ingest-worker`) | Only when `EKIE_INGESTION__ASYNC_ENABLED=true` | Executes queued ingestion/deletion jobs out of the request path |
| C | `monitor.py` (`ekie-monitor`) | Optional | Live per-document progress dashboard |

Ingestion mode is selected by `EKIE_INGESTION__ASYNC_ENABLED` (see 6.2.1):
- **false (default):** the API runs the pipeline inline; Terminal B2 is not needed.
- **true:** the API returns `202` and enqueues jobs; Terminal B2 must be running.

### 6.0 One-Command Control Panel (Recommended)

Instead of launching each process by hand, use the menu-driven control panel at
the repository root. It starts services in their own windows, toggles async mode,
checks health, lists/purges documents, and runs the test suite.

```powershell
cd "D:\Octave\AI training\Enterprise-Knowledge-RAG-System"
.\ekie.ps1
# If PowerShell blocks it: powershell -ExecutionPolicy Bypass -File .\ekie.ps1
```

The menu is mode-aware: option **5 (Start FULL STACK)** launches the API, sync
worker, monitor, and — only when async is enabled — the ingest worker. Option
**6** toggles `EKIE_INGESTION__ASYNC_ENABLED` and reminds you to restart the API.
The sections below document the equivalent manual commands.

### 6.1 Start EKIE API (Terminal A)

```powershell
# From any directory (cwd-safe launcher):
python services/ekie/scripts/start_api.py

# Or after pip install -e services/ekie[...]:
ekie-api

# Manual (must be in services/ekie/):
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -m uvicorn api.app:app --host 0.0.0.0 --port 8001 --app-dir src
Pop-Location
```

### 6.2 Start Production Sync Worker (Terminal B)

```powershell
# From any directory (cwd-safe launcher):
python services/ekie/scripts/start_worker.py

# Or after pip install -e services/ekie[...]:
ekie-worker

# Manual (must be in services/ekie/):
Push-Location services/ekie
..\..\.venv\Scripts\python.exe scripts/production_sync.py
Pop-Location
```

Worker configuration from `.env`:

| Key | Default | Purpose |
|---|---|---|
| `EKIE_SYNC__TARGET_DIRECTORY` | `` | Folder of EKDC-generated Markdown to ingest (set to the EKDC `OUTPUT_DIRECTORY`) |
| `EKIE_SYNC__ALLOWED_EXTENSIONS` | `md` | Restrict ingestion to Markdown files |
| `EKIE_SYNC__TENANT_ID` | `tenant-default` | Tenant identifier |
| `EKIE_SYNC__POLL_INTERVAL_SECONDS` | `300` | How often to scan |
| `EKIE_SYNC__API_BASE_URL` | `http://localhost:8001` | EKIE API endpoint |

### 6.2.1 Asynchronous Ingestion (Durable Job Queue)

By default the API runs the full pipeline (transform → intelligence → chunking →
embedding → publishing) inline within the ingest request. For large documents
this can exceed HTTP read timeouts. Enabling asynchronous ingestion makes the API
persist the source, enqueue a durable job, and return `202 Accepted` immediately;
a dedicated worker pool then executes the pipeline out of the request path with
per-job retries, exponential backoff, and dead-lettering.

Enable it in `.env` and run the ingest worker alongside the API:

```powershell
# 1. In services/ekie/.env:
#    EKIE_INGESTION__ASYNC_ENABLED=true

# 2. Start the ingest worker pool (Terminal B2):
python services/ekie/scripts/start_ingest_worker.py

# Or after pip install -e services/ekie[...]:
ekie-ingest-worker
```

The worker processes both `ingest` and `delete` jobs. Enabling async **requires**
a running ingest worker; otherwise jobs remain queued and never execute.

Source bytes are staged in the Control Plane database (`ingestion_sources` table)
so the worker — a separate process — can read them; they are removed once the job
succeeds. This makes async ingestion work regardless of the asset-storage backend.

| Key | Default | Purpose |
|---|---|---|
| `EKIE_INGESTION__ASYNC_ENABLED` | `false` | Enqueue jobs and return `202` instead of running inline |
| `EKIE_INGESTION__WORKER_CONCURRENCY` | `1` | Worker processes spawned by `start_ingest_worker` |
| `EKIE_INGESTION__CLAIM_BATCH_SIZE` | `1` | Jobs claimed per poll |
| `EKIE_INGESTION__POLL_INTERVAL_SECONDS` | `2.0` | Idle poll interval |
| `EKIE_INGESTION__MAX_ATTEMPTS` | `3` | Whole-job retry budget before dead-letter |
| `EKIE_INGESTION__RETRY_BACKOFF_BASE_SECONDS` | `30.0` | Base delay between job retries |
| `EKIE_INGESTION__RETRY_BACKOFF_MULTIPLIER` | `2.0` | Exponential backoff multiplier |
| `EKIE_INGESTION__RETRY_BACKOFF_MAX_SECONDS` | `900.0` | Backoff cap |
| `EKIE_INGESTION__HEARTBEAT_INTERVAL_SECONDS` | `15.0` | A running worker refreshes its job lock on this interval so a live worker is never mistaken for a crashed one during long stages |
| `EKIE_INGESTION__VISIBILITY_TIMEOUT_SECONDS` | `90.0` | Stale-lock reclaim window. Because live workers heartbeat, this bounds hard-kill recovery: a restarted worker resumes an orphaned job within roughly this many seconds |

**Restart recovery:** stopping the ingest worker with **Ctrl+C** returns its
in-flight job to the queue immediately (without spending a retry), so a restarted
worker resumes it at once. A hard kill (closing the window) instead relies on the
heartbeat + visibility timeout: a live worker keeps its lock fresh every
`HEARTBEAT_INTERVAL_SECONDS`, so a crashed worker's job is reclaimed and resumed
once its lock is older than `VISIBILITY_TIMEOUT_SECONDS` (~90s by default). For
multi-worker pools, keep the timeout a comfortable multiple of the heartbeat
interval.

Poll a document's job state at `GET /v1/documents/{document_id}/job`. Queued,
running, waiting, and dead-letter states are also surfaced in the live monitor.

### 6.3 Monitor Ingestion Progress (Terminal C)

Run the live progress monitor alongside the API and worker to see per-document stage progress, status, and elapsed time:

```powershell
python services/ekie/scripts/monitor.py

# Or after pip install -e services/ekie[...]:
ekie-monitor

# Options:
python services/ekie/scripts/monitor.py --tenant-id tenant-default --refresh 3
python services/ekie/scripts/monitor.py --all   # show all documents
```

The monitor reads the Control Plane directly (no API call required) and refreshes every 3 seconds. It shows one row per document with the following columns:

| Column | Meaning |
|--------|---------|
| **Document** | Source file name. |
| **T I C E P** | Per-stage pipeline bar: `x` = stage complete, `.` = stage pending. |
| **Status** | See the status states below. |
| **Stage Metrics** | Per-stage counters for completed stages, one stage per line (decoded below). |
| **Last** | Elapsed time since the most recent stage asset was written for that document. |

**Status states:**

| Status | Meaning |
|--------|---------|
| `complete` | All five stages done. |
| `>> <stage> <done>/<total> <pct>%` | **Running now** with live intra-stage progress — e.g. `>> E 128/260 49%` while embedding chunks, `>> P 0/258` while publishing vectors. |
| `waiting · resume <stage> [next / #N in line]` | Partially processed on an earlier attempt and **queued to resume** at the first incomplete stage. `[next]` means it is first in the worker's claim order; `[#N in line]` shows how many jobs are ahead; `[…, in 40s]` appears when a retry backoff is still counting down. |
| `queued [#N in line]` | Not yet started; the bracket shows its position in the claim order. |
| `dead-letter xN` | Retries exhausted after N attempts. |

**Navigation:** the monitor renders only the rows that fit the terminal and is
scrollable — use **↑/↓** (row), **PgUp/PgDn** (page), **Home/End** (jump), **f**
to toggle FOLLOW (auto-pin to the top/active rows) versus SCROLL, and **q** (or
**Ctrl+C**) to quit. A footer shows the visible range and current mode.

The header panel adds an overall progress bar with percentage and counts per
status (complete / running / waiting / queued / dead-letter) plus estimated
remaining documents. Live within-stage progress (embedding and publishing batch
counts) is published to the Control Plane as each batch completes, so the Status
column advances `E 1/260 → 260/260` in real time. A categorized Legend panel at
the bottom explains every symbol.

**Pipeline stages (`T I C E P`):**

| Stage | Letter | Meaning |
|-------|--------|---------|
| Transform | `T` | Document → Markdown conversion |
| Intelligence | `I` | Structure / section analysis |
| Chunking | `C` | Splitting into chunks |
| Embedding | `E` | Vector embedding generation |
| Publish | `P` | Writing vectors to Qdrant |

**Stage Metrics** — e.g. `T:168467ch I:291§ 25201t 0tbl 10cb en C:260ch 24451t` decodes as:

- **T** (Transform): `ch` = characters in the generated Markdown.
- **I** (Intelligence): `§` = sections, `t` = tokens, `tbl` = tables, `cb` = code blocks, then the detected language (e.g. `en`).
- **C** (Chunking): `ch` = chunks produced, `t` = total tokens across chunks.
- **E** (Embedding): `em` = embeddings created, `t` = total tokens embedded, `b` = batches, `d` = embedding dimension.
- **P** (Publish): `v` = vectors upserted, `✓` = vectors verified present, `b` = batches.

A condensed version of this legend is always shown in the monitor window itself.

### 6.4 Deleting Documents and Cleaning Up

Deletion is a hard delete: it purges the document's vectors from the vector
store and removes its Control Plane rows (assets, workflows, and processing
state cascade). The sync worker does this automatically when a source file is
removed. To delete one document directly:

```powershell
Invoke-RestMethod -Method Delete `
  -Uri "http://localhost:8001/v1/documents/<document-id>?force=false" `
  -Headers @{ "X-Tenant-ID" = "tenant-default" }
```

For bulk cleanup — including **orphaned** documents left behind after
`EKIE_SYNC__TARGET_DIRECTORY` is repointed at a new folder — use the maintenance
tool (`ekie-purge`):

```powershell
python services/ekie/scripts/purge_documents.py --list
python services/ekie/scripts/purge_documents.py --orphaned --force --yes
python services/ekie/scripts/purge_documents.py --drop-empty-repositories --yes
```

The tool purges the matching documents and their Qdrant vectors, prompting for
confirmation unless `--yes` is given.

### 6.5 Recovering Failed (Dead-Letter) Jobs

When an async job exhausts its retries it moves to `dead_letter` and stops. After
fixing the underlying cause, requeue it so a worker resumes it (the orchestrator
is resumable — it re-runs only the incomplete stages):

```powershell
# Inspect failed / dead-lettered jobs
python services/ekie/scripts/requeue_jobs.py --list

# Requeue one job (by job id or document id), or every dead-lettered job
python services/ekie/scripts/requeue_jobs.py --job-id <id>
python services/ekie/scripts/requeue_jobs.py --document-id <id>
python services/ekie/scripts/requeue_jobs.py --all-dead
```

Only requeue jobs whose cause is fixed. Do **not** requeue a job whose document
was deleted (`transform:not_found`) — the worker now auto-cancels such orphans,
and purging the document is the correct action.

**Recovering documents whose payloads were lost:** if a document dead-lettered
with `markdown payload unavailable` on an older in-memory build, its stage
payloads cannot be recovered. After upgrading to persistent storage (Section
4.3) and restarting the API and worker, reset and re-ingest it from the
Control-Plane-stored source:

```powershell
python services/ekie/scripts/recover_lost_payload_docs.py
```

This clears each affected document's stale stage assets, processing state, and
workflow rows (keeping the document and its stored source) and requeues it so the
worker re-runs it cleanly onto persistent storage. If a document no longer has a
stored source, delete it and re-add the source file so the sync worker
re-discovers it.

---

## 7. Ingestion Verification Checklist

### 7.1 API Health

```powershell
Invoke-RestMethod http://localhost:8001/health/live
# Expected: { status: "ok", service: "ekie" }

Invoke-RestMethod http://localhost:8001/health/ready
# Expected: { status: "ready", service: "ekie" }
```

### 7.2 Run First Ingest (Manual)

```powershell
# 1. Get repository ID from Control Plane:
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -c "
from config.settings import get_settings
from domain.control_plane import ControlPlaneDatabase, Repository
db = ControlPlaneDatabase(get_settings().control_plane)
with db.session() as s:
    repos = s.query(Repository).all()
    [print(r.id, r.name, r.uri) for r in repos]
"
Pop-Location

# 2. Trigger ingestion for a repository:
$headers = @{ 'X-Tenant-ID' = 'tenant-default'; 'Content-Type' = 'application/json' }
$body = '{"sync_before_ingest": true, "max_documents": 5}'
Invoke-RestMethod -Method Post -Uri 'http://localhost:8001/v1/repositories/<repo-id>/ingest' -Headers $headers -Body $body | ConvertTo-Json -Depth 10
```

### 7.3 SQL Verification

```powershell
sqlcmd -S "localhost\MSSQLSERVER2022" -E -C -d ekrag_control_plane -Q "
SELECT TOP 5 id, source_path, status, updated_at FROM documents WHERE tenant_id='tenant-default' ORDER BY updated_at DESC;
SELECT asset_type, COUNT(*) as cnt FROM assets WHERE tenant_id='tenant-default' GROUP BY asset_type;
"
```

### 7.4 Qdrant Verification

```powershell
Invoke-RestMethod http://localhost:6333/collections | ConvertTo-Json -Depth 5

$body = '{ "limit": 2, "with_payload": true, "with_vector": false }'
Invoke-RestMethod -Method Post -Uri 'http://localhost:6333/collections/enterprise_documents/points/scroll' -ContentType 'application/json' -Body $body | ConvertTo-Json -Depth 8
```

### 7.5 Acceptance Report (Full Automated Check)

```powershell
Push-Location services/ekie
..\..\.venv\Scripts\python.exe scripts/acceptance_report.py --tenant-id tenant-default
Pop-Location
# Look for "accepted": true in the JSON output.
```

---

## 8. Production Hardening

### 8.1 Required .env changes for production

```dotenv
# Switch to production mode — enables MinIO storage backend
EKIE_ENVIRONMENT=production

# MinIO credentials (use real values, not defaults)
EKIE_STORAGE__ENDPOINT=localhost:9005
EKIE_STORAGE__ACCESS_KEY=<real-access-key>
EKIE_STORAGE__SECRET_KEY=<real-secret-key>

# Enable authorization enforcement
EKIE_SECURITY__REQUIRE_AUTHENTICATION=false  # set true when API keys are provisioned
EKIE_SECURITY__ENFORCE_AUTHORIZATION=true

# LangGraph orchestrator + Langfuse tracing
EKIE_ORCHESTRATION__RUNNER=langgraph
EKIE_ORCHESTRATION__ENABLE_TRACING=true
EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true
EKIE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY=pk-lf-...
EKIE_OBSERVABILITY__LANGFUSE_SECRET_KEY=sk-lf-...

# HuggingFace models — enable offline mode after both models are downloaded
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
HF_HUB_DISABLE_SYMLINKS_WARNING=1

# LLM analysis (enable only after Qwen2.5-7B-Instruct is downloaded)
EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS=true

# Keep classification downgrade disabled
EKIE_GOVERNANCE__ALLOW_CLASSIFICATION_DOWNGRADE=false
```

### 8.2 Offline Mode (after first model download)

```dotenv
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

### 8.3 Asset Storage in Production

EKIE selects the asset backend automatically:
- **Local filesystem** (`LocalFileAssetStorage`) in `local` mode — assets persist
  on disk under `EKIE_STORAGE__LOCAL_PATH` (default `storage/assets`) and survive
  restarts.
- **MinIO** (`MinIOAssetStorage`) when `EKIE_ENVIRONMENT` is not `local` **and**
  `EKIE_STORAGE__ENDPOINT` is non-empty — for multi-node / durable object storage.

Use MinIO (or another shared store) when running more than one node, so all
workers share one asset store. See [Section 4.3](#43-storage-configuration-assets).

---

## 9. Pre-Production Cleanup

Run before deploying to a clean production environment:

```powershell
python services/ekie/scripts/cleanup_dev_artifacts.py
# or:
ekie-cleanup
```

This removes:
- `services/ekie/storage/acceptance_report_*.json`
- `services/ekie/storage/qdrant_delete_validation_*.json`
- `services/ekie/storage/qdrant/` (local Qdrant state)
- All `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` trees

This does NOT remove: `.env`, source code, installed packages, or HuggingFace model cache.

---

## 10. Upgrade and Rollback

### 10.1 Upgrade

1. Pull latest code: `git pull`
2. Re-install dependencies: `pip install -e "services/ekie[dev,mssql,storage]"`
3. Re-apply schema: `ekie-setup` or run `db.create_all()` (safe to re-run)
4. Restart API and worker

### 10.2 Emergency Rollback (profile swap)

```powershell
# Switch to last known good config profile:
Copy-Item services/ekie/.env.profile.rollback-last-known-good services/ekie/.env -Force
# Restart API and worker
```

### 10.3 Vector Collection Mismatch After Model Change

If you change `EKIE_EMBEDDING__DEFAULT_MODEL` or `EKIE_EMBEDDING__DIMENSION`, existing Qdrant collections may be incompatible. Resolution:

1. Delete the old collection in Qdrant.
2. Set `EKIE_PUBLISHING__CREATE_MISSING_COLLECTIONS=true`.
3. Replay all documents: `POST /v1/documents/{id}/replay` or re-run repository ingest.

---

## 11. Known Gaps and Roadmap

| Gap | Impact | Planned resolution |
|---|---|---|
| No Alembic schema migrations | Schema changes require `db.create_all()` or manual DDL | P1: Add Alembic |
| In-memory workflow checkpointing | Workflow recovery after API crash requires replay | P1: Wire Redis checkpoint backend |
| MinIO HA not configured | Single MinIO instance is a single point of failure | P2: Deploy MinIO in distributed mode |
| No horizontal API scaling | Single API process | P2: Load balancer + replica config |
| Windows-only automation scripts | Linux/macOS operators need shell equivalents | P2: Add bash/Makefile equivalents |
| Langfuse SDK pinned to v2.x | langfuse 3.x/4.x OTEL protocol not compatible with local self-hosted stack | Track Langfuse self-hosted OTEL support; upgrade when stable |

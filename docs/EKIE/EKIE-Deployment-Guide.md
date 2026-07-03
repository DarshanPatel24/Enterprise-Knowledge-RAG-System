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
| Tesseract OCR | When `EKIE_TRANSFORMATION__OCR_ENABLED=true` (image OCR) |

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
$env:MSSQL_SA_PASSWORD = ""          # leave empty for Windows Auth
$env:LANGFUSE_DB_USER = "langfuse"
$env:LANGFUSE_DB_PASSWORD = "langfuse"
$env:LANGFUSE_NEXTAUTH_SECRET = "change-in-production"
$env:LANGFUSE_SALT = "change-in-production"
```

### 2.2 Start Core Infrastructure

```powershell
docker compose -f docker-compose.local.yml up -d qdrant minio mssql redis
```

Wait for healthy status:

```powershell
docker compose -f docker-compose.local.yml ps
# All four services should show "Up" before proceeding.
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

If using Windows Authentication against a local named instance:

```powershell
sqlcmd -S "localhost\MSSQLSERVER2022" -E -C -Q "IF DB_ID('ekrag_control_plane') IS NULL CREATE DATABASE ekrag_control_plane;"
```

If using Docker MSSQL with SQL auth:

```powershell
sqlcmd -S "localhost,1433" -U sa -P "<sa-password>" -C -Q "IF DB_ID('ekrag_control_plane') IS NULL CREATE DATABASE ekrag_control_plane;"
```

### 2.5 Optional: Start Langfuse (Observability)

Only required when `EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true`:

```powershell
docker compose -f docker-compose.local.yml up -d clickhouse langfuse-db langfuse
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
# Core service + all production extras
pip install -e "services/ekie[dev,mssql,storage,richmedia]"
pip install -e packages/contracts

# Optional: HuggingFace embedding / intelligence
pip install langchain-huggingface sentence-transformers torch transformers accelerate

# Optional: Ollama embedding / intelligence
pip install langchain-ollama
```

### 3.3 Automated One-Command Setup

The setup script performs steps 2–5 automatically:

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
| `EKIE_SYNC__TARGET_DIRECTORY` | Folder to watch for documents | `D:\Enterprise\Documents` |
| `EKIE_SYNC__TENANT_ID` | Default tenant identifier | `tenant-prod` |

### 4.3 Storage Configuration (MinIO)

| Key | Default | Production value |
|---|---|---|
| `EKIE_STORAGE__ENDPOINT` | `localhost:9000` | `localhost:9005` (or real MinIO host) |
| `EKIE_STORAGE__ACCESS_KEY` | `` | `minioadmin` (or real key) |
| `EKIE_STORAGE__SECRET_KEY` | `` | `minioadmin` (or real secret) |
| `EKIE_STORAGE__BUCKET` | `ekie-assets` | `ekie-assets` |
| `EKIE_ENVIRONMENT` | `local` | `production` (activates MinIO backend) |

**Critical:** MinIO is only used when `EKIE_ENVIRONMENT=production`. In `local` mode the in-memory backend is used and all assets are lost on restart.

### 4.4 Embedding Configuration

| Key | Default | Notes |
|---|---|---|
| `EKIE_EMBEDDING__PROVIDER` | `local` | `local` = hash-based (CI/offline), `huggingface` or `ollama` for real embeddings |
| `EKIE_EMBEDDING__DEFAULT_MODEL` | `local-hash-256` | Use `sentence-transformers/all-MiniLM-L6-v2` for HuggingFace |
| `EKIE_EMBEDDING__DIMENSION` | `256` | Must match model output (384 for all-MiniLM-L6-v2, 768 for nomic-embed-text) |
| `HF_HOME` | `` | Set to absolute path for persistent HF model cache (e.g., `D:\models\hf-cache`) |

### 4.5 Environment Profiles

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
| `EKIE_SYNC__TARGET_DIRECTORY` | `` | Folder to watch |
| `EKIE_SYNC__TENANT_ID` | `tenant-default` | Tenant identifier |
| `EKIE_SYNC__POLL_INTERVAL_SECONDS` | `300` | How often to scan |
| `EKIE_SYNC__API_BASE_URL` | `http://localhost:8001` | EKIE API endpoint |

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

# LangGraph orchestrator for workflow checkpointing
EKIE_ORCHESTRATION__RUNNER=langgraph

# LLM analysis (enable only after model is downloaded and tested)
EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS=false

# Keep classification downgrade disabled
EKIE_GOVERNANCE__ALLOW_CLASSIFICATION_DOWNGRADE=false
```

### 8.2 Offline Mode (after first model download)

```dotenv
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

### 8.3 MinIO Storage in Production

EKIE uses MinIO for durable asset storage only when:
- `EKIE_ENVIRONMENT=production` (any value other than `local`)
- `EKIE_STORAGE__ENDPOINT` is non-empty

In `local` mode, InMemoryAssetStorage is always used (data is lost on restart).

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
- `services/ekie/storage/rich_media_benchmark_*.json`
- `services/ekie/storage/qdrant_delete_validation_*.json`
- `services/ekie/storage/qdrant/` (local Qdrant state)
- All `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` trees

This does NOT remove: `.env`, source code, installed packages, or HuggingFace model cache.

---

## 10. Upgrade and Rollback

### 10.1 Upgrade

1. Pull latest code: `git pull`
2. Re-install dependencies: `pip install -e "services/ekie[dev,mssql,storage,richmedia]"`
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

# EK-RAG Installation Guide

> Audience: whoever is setting the system up from a fresh clone. Assumes a Windows host (the reference environment). Notes for macOS/Linux are included where they differ.
> Goal: take you from "I just downloaded the repo" to "I can chat with my documents," step by step, with nothing skipped.

This guide is long on purpose. Do the sections **in order**. Each section ends with a **verification** you should not skip.

---

## 0. Before you begin — how the pieces fit

You will install and start things in this order:

1. **Platform prerequisites** (Docker, SQL Server, Python, Node, optional Ollama).
2. **Infrastructure containers** (Qdrant, Redis, MinIO, Langfuse) via Docker Compose.
3. **EKIE** (ingestion engine) — configure, migrate schema, start API.
4. **EKRE** (retrieval engine) — configure, start API.
5. **EKCP** (chat platform) — configure, start API.
6. **Web UI** — configure, build, start.
7. **EKDC** (document converter) — optional; only if your documents aren't already Markdown.
8. **First end-to-end test** — ingest a document and chat about it.

Each engine runs as its **own process** started from **its own folder**. The repository uses a single Python virtual environment at the root (`.venv`) for the three engines, and a **separate** virtual environment for EKDC.

> **Reality check:** there is no single "one command deploys everything." You will start each engine in its own terminal. This is fine for evaluation and single-node use. For real production hardening, read the [Deployment & Cleanup Guide](05-deployment-and-cleanup-guide.md) first.

---

## 1. Platform prerequisites

Install these **before anything else**.

### 1.1 Docker Desktop (required)
Runs Qdrant, Redis, MinIO, and Langfuse.
- Download: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) (or Mac/Linux).
- Windows: enable the **WSL 2** backend in Docker settings.
- Verify:
  ```powershell
  docker --version
  docker compose version
  ```

### 1.2 Microsoft SQL Server (required for EKIE)
EKIE's control plane. The reference setup uses a **Windows-native** instance (`localhost\MSSQLSERVER2022`) with Windows Authentication — it is intentionally **not** a Docker container.
- Install **SQL Server 2022 Developer Edition** and **SQL Server Management Studio (SSMS)** (optional but handy).
- Install the **ODBC Driver 18 for SQL Server** (EKIE connects via `pyodbc`).
- Verify the instance is running (SQL Server Configuration Manager → SQL Server Services).
- *Alternative:* you can run SQL Server in Docker (`mcr.microsoft.com/mssql/server:2022-latest`) and point EKIE at it with a user/password connection; see the [Admin Guide](04-admin-guide.md).

### 1.3 Python 3.11+ (required for EKIE / EKRE / EKCP)
- Download: [python.org](https://www.python.org/downloads/) (3.11 or 3.12).
- Verify: `python --version`.

### 1.4 Node.js 20+ LTS (required for the Web UI)
- Download: [nodejs.org](https://nodejs.org/) (20 LTS or newer).
- Verify: `node --version` and `npm --version`.

### 1.5 Ollama (optional, recommended for local LLM + embeddings)
- Download: [ollama.com](https://ollama.com/).
- Pull a chat model and an embedding model, e.g.:
  ```powershell
  ollama pull llama3.1
  ollama pull nomic-embed-text
  ```
- Verify: `ollama list` and that `http://localhost:11434` responds.

> Without Ollama you can still run everything using deterministic/offline defaults (great for evaluation), or a HuggingFace model provider. The engines are provider-abstracted.

### 1.6 EKDC-only system tools (install later, only if using EKDC)
Covered in Section 7: **Tesseract** (OCR), **FFmpeg** (audio/video), **LibreOffice** (complex Word files).

---

## 2. Get the code and create the Python environment

```powershell
# From wherever you keep projects:
cd "D:\Octave\AI training\Enterprise-Knowledge-RAG-System"   # your clone path

# Create and activate the shared engine virtual environment
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

# Install engine dependencies (each engine has its own requirements)
pip install -r requirements.txt                       # shared/root
pip install -r services/ekie/requirements.txt
pip install -r services/ekre/requirements.txt
pip install -r services/ekcp/requirements.txt
pip install -r requirements-dev.txt                   # ruff, mypy, pytest (optional but recommended)
```

**Verification:** `python -c "import fastapi, pydantic; print('ok')"` prints `ok`.

---

## 3. Start the infrastructure (Docker Compose)

### 3.1 Configure the root `.env`
The compose file reads credentials from a root `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and set **strong** values for at least:
- `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
- `REDIS_PASSWORD`
- `LANGFUSE_DB_PASSWORD`, `CLICKHOUSE_PASSWORD`

### 3.2 Bring the stack up
```powershell
docker compose -f docker-compose.local.yml up -d
docker compose -f docker-compose.local.yml ps
```

This starts:
| Service | Host port | Purpose |
|---|---|---|
| Qdrant | 6333 | Vector database |
| Redis | 6379 | Cache (used by Langfuse) |
| MinIO | 9005 (API), 9006 (console) | Object storage |
| Langfuse | 3000 | Observability UI |
| (langfuse-db, clickhouse) | internal | Langfuse's own stores |

### 3.3 Langfuse first-run (optional but recommended)
1. Open `http://localhost:3000`, create an account and a project.
2. Copy the **public** (`pk-lf-…`) and **secret** (`sk-lf-…`) keys — you'll paste them into each engine's `.env`.

> **Port conflict warning:** Langfuse uses **3000**. The Web UI also defaults to 3000. Plan to run the **Web UI on 3001** (Section 6).

**Verification:**
- `http://localhost:6333/dashboard` (Qdrant) loads.
- `http://localhost:9006` (MinIO console) loads and you can log in.
- `http://localhost:3000` (Langfuse) loads.

---

## 4. EKIE — Ingestion Engine (port 8001)

### 4.1 Configure
```powershell
Copy-Item services/ekie/.env.example services/ekie/.env
```
Open `services/ekie/.env` and set:
- **Control plane (SQL Server):**
  - `EKIE_CONTROL_PLANE__HOST=localhost\MSSQLSERVER2022`
  - `EKIE_CONTROL_PLANE__TRUSTED_CONNECTION=true` (Windows auth) — or set `USER`/`PASSWORD` for SQL auth.
- **Object storage (MinIO):** `EKIE_STORAGE__ENDPOINT=localhost:9005`, `ACCESS_KEY`, `SECRET_KEY` (match the root `.env`), `BUCKET=ekie-assets`, `SECURE=false`.
- **Embedding/vector providers:** for a fully local, dependency-free first run use the deterministic **local** providers:
  - `EKIE_EMBEDDING__PROVIDER=local`
  - `EKIE_PUBLISHING__PROVIDER=qdrant` (to write into Qdrant) or `local` (in-memory, for a pure smoke test).
  - For real embeddings via Ollama/HuggingFace, set the provider and model accordingly (see the [Admin Guide](04-admin-guide.md)).
- **Observability (optional):** `EKIE_OBSERVABILITY__LANGFUSE_ENABLED`, `LANGFUSE_URL`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`.

### 4.2 Initialize (schema + storage)
EKIE ships an initializer that creates the database, runs migrations, and provisions the MinIO bucket:
```powershell
python services/ekie/scripts/setup.py
```
This performs prerequisite checks, ensures the SQL Server database exists, runs the additive schema migrations (`run_migrations()`), and creates the `ekie-assets` bucket.

> If `setup.py` cannot reach SQL Server, confirm the instance name, that TCP is enabled, and that ODBC Driver 18 is installed.

### 4.3 Start the API
```powershell
python services/ekie/scripts/start_api.py     # serves on http://0.0.0.0:8001
```

**Verification:**
```powershell
Invoke-WebRequest http://localhost:8001/health/live -UseBasicParsing | Select-Object -ExpandProperty Content
# {"status":"ok","service":"ekie"}
Invoke-WebRequest http://localhost:8001/health/ready -UseBasicParsing
```

---

## 5. EKRE — Retrieval Engine (port 8002)

### 5.1 Configure
```powershell
Copy-Item services/ekre/.env.example services/ekre/.env
```
Set in `services/ekre/.env`:
- **Qdrant (must match EKIE's):** `EKRE_QDRANT__HOST=localhost`, `EKRE_QDRANT__PORT=6333`.
- **Retrieval mode (fast local dev):** use the offline deterministic path to avoid loading a model on the first query:
  - `EKRE_WORKERS__CONNECTOR=inmemory` (or `qdrant` to search the real store)
  - `EKRE_WORKERS__QUERY_EMBEDDER=local_hash` (or `langchain` for real embeddings)
  - `EKRE_QUERY__ENABLE_LLM_INTERPRETER=false`
- **Security context (optional):** `EKRE_SECURITY__REQUIRE_SIGNED_CONTEXT`, `CONTEXT_SIGNING_SECRET` if you enable signed contexts.
- **Observability (optional):** Langfuse keys.

> **Important:** for EKRE to return *real* answers from your documents, set `EKRE_WORKERS__CONNECTOR=qdrant` and a query embedder that matches the embedding model EKIE used to publish (the distance metric and model are inherited from the Qdrant collection).

### 5.2 Start the API
```powershell
python services/ekre/scripts/start_api.py     # serves on http://127.0.0.1:8002
```

**Verification:**
```powershell
Invoke-WebRequest http://localhost:8002/health/live -UseBasicParsing
Invoke-WebRequest http://localhost:8002/v1/readiness -UseBasicParsing
```

---

## 6. EKCP — Chat Platform (port 8003)

### 6.1 Configure
```powershell
Copy-Item services/ekcp/.env.example services/ekcp/.env
```
Set in `services/ekcp/.env`:
- **Gateway auth (recommended ON):**
  - `EKCP_SECURITY__REQUIRE_GATEWAY_AUTH=true`
  - `EKCP_SECURITY__GATEWAY_AUTH_TOKEN=<choose-a-strong-token>` — the Web UI must present this.
- **Security context gate:** `EKCP_SECURITY__REQUIRE_SECURITY_CONTEXT=true` (every chat needs `user_id/tenant_id/clearance`).
- **Knowledge (connect to EKRE):**
  - `EKCP_KNOWLEDGE__ENABLED=true`
  - `EKCP_KNOWLEDGE__BASE_URL=http://localhost:8002`
- **Model gateway:** `EKCP_MODEL__RUNTIME=deterministic` for an offline smoke test, or `langchain` with an Ollama/HuggingFace model for real answers.
- **Governance role (so memory/agent calls are authorized):** `EKCP_GOVERNANCE__DEFAULT_ROLE=power_user` for evaluation.
- **Optional Redis / SQL Server** for real session/conversation persistence (defaults are in-memory).
- **Observability (optional):** Langfuse keys.

### 6.2 Start the API
```powershell
python services/ekcp/scripts/start_api.py     # serves on host/port from .env (default 8003)
```

**Verification:**
```powershell
Invoke-WebRequest http://localhost:8003/health/live -UseBasicParsing
Invoke-WebRequest http://localhost:8003/v1/readiness -UseBasicParsing
```

---

## 7. EKDC — Document Converter (optional; only if documents aren't Markdown)

EKDC has its **own virtual environment** and **its own system tools**.

### 7.1 System tools
- **Tesseract OCR** — [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki). Add to `PATH` or set `EKDC_TESSERACT_CMD`.
- **FFmpeg** — [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/) (`ffmpeg-release-essentials.zip`); add `…\ffmpeg\bin` to `PATH`. Verify `ffmpeg -version`.
- **LibreOffice** — [libreoffice.org](https://www.libreoffice.org/download/); point `DOCLING_LIBREOFFICE_CMD` at `soffice.exe`.

### 7.2 Python environment + config
```powershell
cd services/ekdc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env    # if a template exists; otherwise create .env
```
Edit `services/ekdc/.env` (see the full table in the [Admin Guide](04-admin-guide.md)). At minimum set:
- `INPUT_DIRECTORY=` a folder where you will drop source files.
- `OUTPUT_DIRECTORY=` a **separate** folder for the generated Markdown (must not be nested inside the input).
- `EKDC_OCR_ENGINE=tesseract`, `EKDC_OCR_LANGUAGES=eng`.
- `EKDC_DOCLING_IMAGE_MODE=referenced` (best for RAG).
- Leave `EKDC_DESCRIBE_IMAGES=false` and `EKDC_OFFLINE=false` for the first run.

### 7.3 Run it
```powershell
python agent.py     # foreground; converts existing files, then watches for new ones
```
It logs to the console and `services/ekdc/ekdc_agent.log`. Stop with `Ctrl+C`.

> First run may download models (Whisper/HuggingFace) to `services/ekdc/storage/`. Once cached, set `EKDC_OFFLINE=true` for air-gapped operation.

**Verification:** drop a `.pdf` into `INPUT_DIRECTORY`; a `.pdf.md` (and possibly a `…_artifacts/` folder) appears in `OUTPUT_DIRECTORY`.

> Wire EKDC's `OUTPUT_DIRECTORY` to EKIE's ingestion source so converted Markdown flows into the pipeline (see the [Admin Guide](04-admin-guide.md), "Connecting EKDC to EKIE").

---

## 8. Web UI — the chat app (dev port 3001)

### 8.1 Install and configure
```powershell
cd apps/web-ui
npm install
Copy-Item .env.local.example .env.local
```
Edit `apps/web-ui/.env.local`:
- `NEXT_PUBLIC_EKCP_URL=http://localhost:8003`
- Leave tenant/user/clearance blank here — they are set per-user at runtime on the **Settings** screen (and the API key too).

### 8.2 Run
Development (hot reload):
```powershell
npm run dev -- --port 3001
```
Production build + serve:
```powershell
npm run build
npm run start -- --port 3001
```

### 8.3 Configure your session in the browser
1. Open `http://localhost:3001`.
2. The home page shows **EKCP connectivity** — it should say **Online**.
3. Go to **Settings** and enter:
   - **EKCP API URL:** `http://localhost:8003`
   - **API key:** the same value as `EKCP_SECURITY__GATEWAY_AUTH_TOKEN`.
   - **Tenant ID / User ID:** e.g., `tenant-a` / `u-1`.
   - **Clearance:** e.g., `internal`.
4. Save. Open **Chat** and ask a question.

**Verification:** you can send a message and see the answer stream in. If documents are ingested and EKRE is wired, you also see **citation cards**.

---

## 9. First end-to-end test

1. **Ingest a document** (pick one path):
   - Via EKDC: drop a file into `INPUT_DIRECTORY`, then point EKIE at the converted Markdown and ingest it.
   - Directly via EKIE's ingestion API (see the [EKIE Deployment Guide](../EKIE/EKIE-Deployment-Guide.md) for the exact `/v1/documents/{id}/ingest` call).
2. **Confirm vectors landed:** open the Qdrant dashboard (`http://localhost:6333/dashboard`) and check the collection has points.
3. **Ask about it** in the Web UI. You should get a grounded answer with a **citation card** pointing at the source path.
4. **Confirm tracing (optional):** open Langfuse and see the trace.

If all four succeed, your installation is complete. 🎉

---

## 10. Start/stop cheat-sheet

Every time you want the full system up (five terminals; run the Web UI on 3001):
```powershell
# Terminal 1 — infrastructure
docker compose -f docker-compose.local.yml up -d

# Terminal 2 — EKIE
.\.venv\Scripts\Activate.ps1; python services/ekie/scripts/start_api.py

# Terminal 3 — EKRE
.\.venv\Scripts\Activate.ps1; python services/ekre/scripts/start_api.py

# Terminal 4 — EKCP
.\.venv\Scripts\Activate.ps1; python services/ekcp/scripts/start_api.py

# Terminal 5 — Web UI
cd apps/web-ui; npm run start -- --port 3001

# Terminal 6 (optional) — EKDC
cd services/ekdc; .\.venv\Scripts\Activate.ps1; python agent.py
```
Stop each with `Ctrl+C`; stop infrastructure with `docker compose -f docker-compose.local.yml down`.

> This many-terminals workflow is the current reality. See the [Deployment & Cleanup Guide](05-deployment-and-cleanup-guide.md) for how to make it a proper managed deployment.

---

## 11. Common install problems

| Problem | Fix |
|---|---|
| `setup.py` can't connect to SQL Server | Check instance name, enable TCP/IP, install ODBC Driver 18, confirm Windows auth. |
| MinIO bucket errors | Ensure MinIO is up (`9005`), and `EKIE_STORAGE__*` matches the root `.env` credentials. |
| EKCP chat returns 401 | The Web UI API key must equal `EKCP_SECURITY__GATEWAY_AUTH_TOKEN`. |
| EKCP chat returns 403 | Set a valid security context (tenant/user/clearance) in Settings; tenant must match. |
| No citations in answers | Set `EKCP_KNOWLEDGE__ENABLED=true`, start EKRE, and ingest documents. |
| Web UI won't start (port busy) | Langfuse owns 3000 — use `--port 3001`. |
| EKRE first query hangs | It's loading a HuggingFace model; use `EKRE_WORKERS__QUERY_EMBEDDER=local_hash` for dev. |
| EKDC does nothing | Verify `INPUT_DIRECTORY`/`OUTPUT_DIRECTORY` and that Tesseract/FFmpeg are on `PATH`. |

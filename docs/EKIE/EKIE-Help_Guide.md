# EKIE — Enterprise Knowledge Ingestion Engine

## Complete Documentation & Operations Guide

> **Version:** 1.0
> **Status:** Approved
> **Audience:** Engineers, DevOps, Platform Operators
> **Last Updated:** 2026-07-03

---

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Architecture Overview](#2-architecture-overview)
- [3. Prerequisites](#3-prerequisites)
- [4. Project Structure](#4-project-structure)
- [5. Environment Setup](#5-environment-setup)
- [6. Configuration Reference](#6-configuration-reference)
- [7. Infrastructure Setup](#7-infrastructure-setup)
- [8. Running the Service](#8-running-the-service)
- [9. API Reference](#9-api-reference)
- [10. Ingestion Pipeline Stages](#10-ingestion-pipeline-stages)
- [11. Domain Modules Deep Dive](#11-domain-modules-deep-dive)
- [12. Security & Governance](#12-security--governance)
- [13. Plugin SDK](#13-plugin-sdk)
- [14. Observability & Logging](#14-observability--logging)
- [15. Validation & Readiness](#15-validation--readiness)
- [16. Demo Scripts](#16-demo-scripts)
- [17. Testing](#17-testing)
- [18. Deployment Guide](#18-deployment-guide)
- [19. Troubleshooting](#19-troubleshooting)
- [20. Glossary](#20-glossary)
- [21. PM Owner Runbook](#21-pm-owner-runbook)

---

## 1. Introduction

### 1.1 What is EKIE?

EKIE (Enterprise Knowledge Ingestion Engine) is a dedicated enterprise platform that transforms heterogeneous enterprise documents into governed, versioned, traceable, and AI-ready knowledge assets. It is the ingestion layer of the three-engine EK-RAG architecture.

### 1.2 What EKIE Does

| Capability | Description |
|---|---|
| Document conversion (upstream) | The EKDC agent converts any source format (PDF, DOCX, PPTX, HTML, CSV, images, audio, video) to Markdown before ingestion (`services/ekdc`) |
| Repository synchronization | Continuously syncs the Markdown output folder (and other repositories) into Document Digital Twins |
| Document transformation | Normalizes incoming Markdown into canonical Markdown assets (front matter, Unicode normalization, validation) |
| Document intelligence | Extracts metadata, detects language, classifies content, identifies sensitive data |
| Intelligent chunking | Splits Markdown into semantically meaningful chunks preserving structure |
| Embedding generation | Generates vector embeddings via local, Ollama, or HuggingFace providers (active: `BAAI/bge-base-en-v1.5`) |
| Vector publishing | Publishes embeddings to Qdrant with mandatory metadata enforcement |
| Workflow orchestration | Runs the full pipeline as a checkpointed, resumable graph |
| Security & governance | RBAC/ABAC authorization, audit logging, classification enforcement |

### 1.3 What EKIE Does NOT Do

EKIE strictly owns ingestion. The following capabilities belong to downstream engines:

- **Retrieval, semantic search, query planning** → EKRE (Retrieval Engine)
- **Chat interfaces, LLM orchestration, conversations** → EKCP (Chat Platform)

### 1.4 Key Principles

1. **Canonical Representation** — Every document becomes Markdown before further processing.
2. **Immutable Assets** — Derived artifacts are never modified; changes create new versions.
3. **Deterministic Processing** — Same input + same configuration = same output.
4. **Configuration Over Code** — Behavior is driven by environment variables, not hardcoded values.
5. **Local-First** — Runs entirely offline with self-hosted infrastructure by default.

---

## 2. Architecture Overview

### 2.1 System Topology

```
Enterprise Repositories (any format: PDF, DOCX, PPTX, HTML, CSV, images, audio, video)
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│      EKDC — Enterprise Knowledge Document Converter          │
│      Converts every source file to Markdown (structure kept)  │
└─────────────────────────────────────────────────────────────┘
       │  Markdown (.md) files
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    EKIE Platform                             │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐       │
│  │   Sync   │→ │ Transformation│→ │   Intelligence   │       │
│  │ Framework│  │   Pipeline    │  │     Engine        │       │
│  └──────────┘  └──────────────┘  └──────────────────┘       │
│       │               │                   │                  │
│       ▼               ▼                   ▼                  │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐       │
│  │ Chunking │→ │  Embedding   │→ │   Publishing     │       │
│  │  Engine  │  │    Engine     │  │     Engine        │       │
│  └──────────┘  └──────────────┘  └──────────────────┘       │
│                                                              │
│  ┌───────────────────────────────────────────────────┐       │
│  │          Workflow Orchestrator (LangGraph)         │       │
│  └───────────────────────────────────────────────────┘       │
│                                                              │
│  ┌───────────────┐  ┌──────────┐  ┌────────────────┐        │
│  │ Control Plane │  │  Asset   │  │   Security &   │        │
│  │   (MS SQL)    │  │ Storage  │  │  Governance    │        │
│  └───────────────┘  │ (MinIO)  │  └────────────────┘        │
│                      └──────────┘                            │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
  AI-Ready Knowledge Assets → EKRE → EKCP → Enterprise AI Apps
```

### 2.2 Data Flow

```
Source Document (any format)
  → EKDC Conversion (any format → Markdown, folder structure preserved)
    → Repository Sync of Markdown (Digital Twin created/updated)
      → Transformation (Markdown intake → canonical Markdown asset)
        → Intelligence (metadata extraction, classification, quality scoring)
          → Chunking (Markdown → semantic chunks with breadcrumb context)
            → Embedding (chunks → vector embeddings)
              → Publishing (embeddings → Qdrant with verified metadata)
```

### 2.3 Control Plane Database Schema

The Control Plane (Microsoft SQL Server) is the single source of truth for all ingestion state:

| Table | Purpose |
|---|---|
| `repositories` | Registered enterprise source repositories |
| `documents` | Document Digital Twins with version, hash, classification |
| `assets` | Immutable versioned generated assets (markdown, intelligence, chunks, embeddings, vectors) |
| `asset_lineage` | Directed lineage edges between parent and derived assets |
| `workflows` | Ingestion workflow execution records |
| `processing_state` | Per-stage processing status with retry counts |

---

## 3. Prerequisites

### 3.1 Software Requirements

| Software | Version | Purpose |
|---|---|---|
| **Python** | 3.11+ | Runtime |
| **Docker & Docker Compose** | Latest | Infrastructure services |
| **Git** | Latest | Version control |
| **ODBC Driver 18 for SQL Server** | Latest | MS SQL Server connectivity |

### 3.2 Optional Software

| Software | Version | Purpose |
|---|---|---|
| **Ollama** | Latest | Alternative local LLM and embedding model server |
| **Node.js** | 18+ | Web UI (separate `apps/web-ui/` project) |
| **EKDC agent** | Latest | Converts non-Markdown source files to Markdown for EKIE to ingest (`services/ekdc`) |

### 3.3 Hardware Recommendations

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32 GB (required for HuggingFace model inference) |
| Disk | 40 GB free | 100+ GB SSD (HuggingFace model weights ~500 MB embedder + ~3 GB LLM when analysis enabled) |
| GPU | Not required | NVIDIA GPU strongly recommended for HuggingFace model performance |

---

## 4. Project Structure

```
Enterprise-Knowledge-RAG-System/
├── docs/
│   └── EKIE/
│       ├── EKIE-handbook.md          # Architecture handbook (22 chapters)
│       └── EKIE-Help_Guide.md        # This document
├── packages/
│   └── contracts/                    # Shared cross-engine Pydantic v2 schemas
│       └── src/
├── services/
│   └── ekie/
│       ├── .env.example              # Configuration template (180 variables)
│       ├── .env.profile.ollama       # Ollama profile
│       ├── .env.profile.huggingface  # HuggingFace profile
│       ├── .env.profile.hybrid       # Hybrid profile
│       ├── .env.profile.rollback-last-known-good # rollback profile
│       ├── pyproject.toml            # Project metadata and dependencies
│       ├── scripts/                  # Automation, demo, and validation scripts
│       │   ├── setup.py              # One-command first-time environment setup
│       │   ├── start_api.py          # cwd-safe API launcher (ekie-api)
│       │   ├── start_worker.py       # cwd-safe worker launcher (ekie-worker)
│       │   ├── monitor.py            # Live ingestion progress monitor (ekie-monitor)
│       │   ├── cleanup_dev_artifacts.py # Pre-production cleanup (ekie-cleanup)
│       │   ├── production_sync.py    # Continuous folder-polling ingestion worker
│       │   ├── acceptance_report.py  # One-command acceptance evidence report
│       │   ├── validate_qdrant_delete_path.py # Live Qdrant delete-path validation
│       │   ├── demo_sync.py
│       │   ├── demo_transform.py
│       │   ├── demo_intelligence.py
│       │   ├── demo_chunking.py
│       │   ├── demo_embedding.py
│       │   ├── demo_publishing.py
│       │   ├── demo_orchestration.py
│       │   ├── demo_security.py
│       │   └── demo_validation.py
│       ├── src/
│       │   ├── api/                  # FastAPI application layer
│       │   │   ├── app.py            # Application factory
│       │   │   ├── ingestion.py      # Ingestion REST endpoints
│       │   │   ├── health.py         # Health probes (liveness/readiness)
│       │   │   ├── dependencies.py   # Dependency injection
│       │   │   └── middleware.py     # Correlation and tenant middleware
│       │   ├── config/
│       │   │   └── settings.py       # 16 environment-backed settings groups
│       │   ├── composition.py        # Composition root (engine wiring)
│       │   └── domain/               # Core domain logic
│       │       ├── sync/             # Repository synchronization
│       │       ├── transformation/   # Document transformation pipeline
│       │       ├── intelligence/     # Document intelligence engine
│       │       ├── chunking/         # Intelligent chunking engine
│       │       ├── embedding/        # Embedding framework
│       │       ├── publishing/       # Vector publishing engine
│       │       ├── orchestration/    # Workflow orchestration (LangGraph)
│       │       ├── security/         # Auth, RBAC, audit, classification
│       │       ├── plugins/          # Plugin SDK and registry
│       │       ├── validation/       # Pipeline validation and readiness
│       │       ├── control_plane/    # ORM models and database
│       │       ├── storage/          # Immutable asset storage
│       │       └── observability/    # Structured logging and context
│       └── tests/                    # 42 test files
├── docker-compose.local.yml          # Local infrastructure stack
├── requirements.txt                  # Runtime dependencies
└── .env.example                      # Root-level environment template
```

---

## 5. Environment Setup

### 5.1 Clone the Repository

```bash
git clone <repository-url>
cd Enterprise-Knowledge-RAG-System
```

### 5.2 Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 5.3 Install Dependencies

```bash
# Core runtime dependencies
pip install -r requirements.txt

# EKIE service with all production extras
pip install -e "services/ekie[dev,mssql,storage]"

# Required for BAAI/bge-base-en-v1.5 (text embedding model; no image extras needed)
pip install -U sentence-transformers

# Required for HuggingFace intelligence LLM (Qwen/Qwen2.5-3B-Instruct, optional)
pip install langchain-huggingface torch transformers accelerate

# Shared contracts package
pip install -e packages/contracts
```

EKIE ingests Markdown only. Converting other formats (PDF, DOCX, PPTX, HTML, CSV,
images, audio, video) to Markdown is performed upstream by the EKDC agent
(`services/ekdc`); no OCR or rich-media libraries are installed for EKIE.

### 5.4 Configure Environment Variables

```bash
# Copy the EKIE configuration template
cp services/ekie/.env.example services/ekie/.env
```

Edit `services/ekie/.env` and set your local values. The critical values to configure:

For **Windows Authentication** (recommended for local Windows SQL Server):
```dotenv
# Use Windows Auth — no password needed
EKIE_CONTROL_PLANE__HOST=localhost\MSSQLSERVER2022
EKIE_CONTROL_PLANE__PORT=
EKIE_CONTROL_PLANE__TRUSTED_CONNECTION=true

# MinIO object storage (port 9005 matches docker-compose.local.yml)
EKIE_STORAGE__ENDPOINT=localhost:9005
EKIE_STORAGE__ACCESS_KEY=minioadmin
EKIE_STORAGE__SECRET_KEY=minioadmin

# Source folder for ingestion worker
EKIE_SYNC__TARGET_DIRECTORY=D:\Enterprise\Documents
EKIE_SYNC__TENANT_ID=ekie-tenant
```

For **SQL Server Authentication** (Docker container or remote SQL):
```dotenv
EKIE_CONTROL_PLANE__HOST=localhost
EKIE_CONTROL_PLANE__PORT=1433
EKIE_CONTROL_PLANE__USER=sa
EKIE_CONTROL_PLANE__PASSWORD=YourStrongPassword123!
EKIE_CONTROL_PLANE__TRUSTED_CONNECTION=false
```

### 5.5 Install ODBC Driver (MS SQL Server)

**Windows:**
Download and install [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) from Microsoft.

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install msodbcsql18
```

### 5.6 Preflight Change Audit (Required Before Running EKIE)

Before setup or deployment, inventory the current repository state so you know what changed:

```bash
git status --short
```

Interpretation:
1. `M` means modified tracked file.
2. `??` means new untracked file.
3. Missing files from expected paths indicate a deletion or move.

Recommended preflight checklist:
1. Confirm `docs/EKIE/EKIE-Help_Guide.md` is current.
2. Confirm `services/ekie/.env.example` exists and reflects latest options.
3. Confirm `services/ekie/.env.profile.*` profiles exist for operator switching.
4. Confirm ingestion API files are present under `services/ekie/src/api/`.

### 5.7 Files Operators Edit, And What Each Controls

Edit these files for operations; do not edit business logic for routine deployment changes.

| File | Purpose | Typical edits |
|---|---|---|
| `services/ekie/.env` | Active runtime configuration for EKIE process | Provider/model selection, credentials, target directory, tracing toggles |
| `services/ekie/.env.profile.ollama` | Ollama-first profile template | Ollama models, Qdrant settings |
| `services/ekie/.env.profile.huggingface` | HuggingFace-first profile template | HF model IDs, `HF_HOME`, dimensions |
| `services/ekie/.env.profile.hybrid` | Mixed provider template | HF intelligence + Ollama embeddings (or inverse) |
| `services/ekie/.env.profile.rollback-last-known-good` | Fast rollback profile | Restore known good provider/model values |
| `.env` (repo root) | Local container stack variables | Docker service credentials for MinIO and Langfuse |

Operator rule:
1. Copy profile to `services/ekie/.env`.
2. Adjust only env variables required for your environment.
3. Restart service.
4. Run health and smoke ingest checks.

---

## 6. Configuration Reference

> **Note:** This entire section is for **informational reference only**. For your initial setup, you only need to configure the critical variables mentioned in [Section 5.4](#54-configure-environment-variables). You do not need to perform any actions in this section unless you want to customize EKIE's default behavior.

> **Important for operator workflows:** You do **not** edit Python source files (for example `services/ekie/src/config/settings.py`) to change providers or models. The values in code are defaults and validation constraints only. Runtime selection is done in `services/ekie/.env` using `EKIE_*` variables.

EKIE uses a hierarchical, environment-backed configuration system. All values use the `EKIE_` prefix with `__` as the nesting delimiter.

### 6.1 Settings Architecture

The top-level `EkieSettings` class composes 16 subsystem settings groups:

```
EkieSettings
├── app_name: str = "ekie"
├── environment: str = "local"
├── control_plane: ControlPlaneSettings     # MS SQL Server
├── qdrant: QdrantSettings                  # Vector database
├── redis: RedisSettings                    # Cache
├── storage: StorageSettings                # MinIO object storage
├── observability: ObservabilitySettings    # Logging, Langfuse, OTEL
├── sync: SyncSettings                      # Repository sync policy
├── transformation: TransformationSettings  # Document transformation
├── intelligence: IntelligenceSettings      # Document intelligence
├── chunking: ChunkingSettings              # Intelligent chunking
├── embedding: EmbeddingSettings            # Embedding framework
├── publishing: PublishingSettings           # Vector publishing
├── orchestration: OrchestrationSettings    # Workflow orchestration
├── security: SecuritySettings              # Auth and authorization
├── governance: GovernanceSettings          # Audit and classification
├── plugins: PluginSettings                 # Plugin SDK
└── deployment: DeploymentSettings          # NFR and DR targets
```

### 6.2 Infrastructure Settings

#### Control Plane (Microsoft SQL Server)

| Variable | Default | Description |
|---|---|---|
| `EKIE_CONTROL_PLANE__HOST` | `localhost` | SQL Server hostname |
| `EKIE_CONTROL_PLANE__PORT` | `1433` | SQL Server port |
| `EKIE_CONTROL_PLANE__DATABASE` | `ekrag_control_plane` | Database name |
| `EKIE_CONTROL_PLANE__USER` | `sa` | Database user |
| `EKIE_CONTROL_PLANE__PASSWORD` | *(empty)* | Database password (**set this**) |
| `EKIE_CONTROL_PLANE__TRUSTED_CONNECTION` | `false` | Set to true to use Windows Authentication |
| `EKIE_CONTROL_PLANE__DRIVER` | `ODBC Driver 18 for SQL Server` | ODBC driver |
| `EKIE_CONTROL_PLANE__ENCRYPT` | `true` | Enable TLS encryption |
| `EKIE_CONTROL_PLANE__TRUST_SERVER_CERTIFICATE` | `true` | Trust self-signed certs |
| `EKIE_CONTROL_PLANE__URL` | *(none)* | Full SQLAlchemy URL override |

#### Qdrant (Vector Database)

| Variable | Default | Description |
|---|---|---|
| `EKIE_QDRANT__HOST` | `localhost` | Qdrant hostname |
| `EKIE_QDRANT__PORT` | `6333` | Qdrant gRPC port |
| `EKIE_QDRANT__URL` | *(empty)* | Optional full Qdrant URL (used by the LangChain index template); blank = use HOST/PORT |
| `EKIE_QDRANT__API_KEY` | *(empty)* | Optional Qdrant API key for the LangChain index template |
| `EKIE_QDRANT__REQUEST_TIMEOUT_SECONDS` | `30.0` | Request timeout |

#### Redis (Cache)

| Variable | Default | Description |
|---|---|---|
| `EKIE_REDIS__HOST` | `localhost` | Redis hostname |
| `EKIE_REDIS__PORT` | `6379` | Redis port |

#### MinIO (Object Storage)

| Variable | Default | Description |
|---|---|---|
| `EKIE_STORAGE__ENDPOINT` | `localhost:9005` | MinIO endpoint (port 9005 matches docker-compose.local.yml) |
| `EKIE_STORAGE__ACCESS_KEY` | *(empty)* | Access key (**set this**) |
| `EKIE_STORAGE__SECRET_KEY` | *(empty)* | Secret key (**set this**) |
| `EKIE_STORAGE__BUCKET` | `ekie-assets` | Asset storage bucket |
| `EKIE_STORAGE__SECURE` | `false` | Enable HTTPS |

### 6.3 Pipeline Settings

#### Repository Synchronization

| Variable | Default | Description |
|---|---|---|
| `EKIE_SYNC__SCAN_STRATEGY` | `incremental` | `incremental` or `full` scan |
| `EKIE_SYNC__IGNORE_HIDDEN` | `true` | Skip hidden files/directories |
| `EKIE_SYNC__IGNORE_TEMP` | `true` | Skip temporary files |
| `EKIE_SYNC__MAX_FILE_SIZE_BYTES` | `524288000` | Max file size (500 MB) |
| `EKIE_SYNC__ALLOWED_EXTENSIONS` | *(empty = all)* | Comma-separated allowlist |
| `EKIE_SYNC__HASH_ALGORITHM` | `sha256` | Content hash algorithm |
| `EKIE_SYNC__RENAME_DETECTION_ENABLED` | `true` | Detect file renames |
| `EKIE_SYNC__DELETE_PROPAGATION_ENABLED` | `true` | Propagate file deletions |
| `EKIE_SYNC__DEFAULT_CLASSIFICATION` | `internal` | Default security classification |

#### Document Transformation

| Variable | Default | Description |
|---|---|---|
| `EKIE_TRANSFORMATION__NORMALIZE_UNICODE` | `true` | Normalize Unicode text |
| `EKIE_TRANSFORMATION__COLLAPSE_BLANK_LINES` | `true` | Collapse consecutive blank lines |
| `EKIE_TRANSFORMATION__INCLUDE_FRONT_MATTER` | `true` | Include YAML front matter |
| `EKIE_TRANSFORMATION__DEFAULT_LANGUAGE` | `en` | Default document language |

#### Document Intelligence

| Variable | Default | Description |
|---|---|---|
| `EKIE_INTELLIGENCE__DETECT_LANGUAGE` | `true` | Auto-detect language |
| `EKIE_INTELLIGENCE__CLASSIFY_CONTENT` | `true` | Classify document type |
| `EKIE_INTELLIGENCE__DETECT_SENSITIVE_CONTENT` | `true` | Detect PII/sensitive data |
| `EKIE_INTELLIGENCE__HIGH_COMPLEXITY_SECTION_THRESHOLD` | `12` | Section complexity threshold |
| `EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS` | `false` | Enable LLM-based topic analysis (optional, off by default) |
| `EKIE_INTELLIGENCE__LLM_PROVIDER` | `huggingface` | Allowed values: `ollama` or `huggingface` |
| `EKIE_INTELLIGENCE__LLM_MODEL` | `Qwen/Qwen2.5-3B-Instruct` | LLM model name |
| `EKIE_INTELLIGENCE__LLM_BASE_URL` | `http://localhost:11434` | LLM endpoint |
| `EKIE_INTELLIGENCE__LLM_TEMPERATURE` | `0.0` | LLM temperature (deterministic) |

If an unsupported provider value is configured, EKIE fails configuration validation at startup.

> **Note on using HuggingFace locally for Intelligence:** To use a HuggingFace LLM (e.g., `Qwen/Qwen2.5-3B-Instruct`) for topic analysis, install the dependencies (`pip install langchain-huggingface torch transformers accelerate`). Then set `EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS=true`, `EKIE_INTELLIGENCE__LLM_PROVIDER=huggingface`, and update `EKIE_INTELLIGENCE__LLM_MODEL` to your model ID. The model weights will be downloaded and cached in your `HF_HOME` directory.

> **Use a text-generation model, not a vision model.** `EKIE_INTELLIGENCE__LLM_MODEL` must be a text/chat instruct model (loaded as a `text-generation` pipeline), for example `Qwen/Qwen2.5-3B-Instruct`. A **vision-language** model such as `Qwen/Qwen2.5-VL-3B-Instruct` cannot be loaded this way; the analyzer logs `llm_analysis_skipped` and falls back to the deterministic heuristic topic (ingestion still completes). CPU inference on multi-billion-parameter models is slow (minutes per document); use a smaller model, an Ollama backend, or set `ENABLE_LLM_ANALYSIS=false` to skip it. See §19.1.

#### Intelligent Chunking

| Variable | Default | Description |
|---|---|---|
| `EKIE_CHUNKING__DEFAULT_STRATEGY` | `semantic` | Strategy: `semantic`, `section_based`, `heading_based`, `paragraph_based`, `token_based`, `table_based`, `code_based`, `recursive` |
| `EKIE_CHUNKING__TARGET_TOKEN_BUDGET` | `512` | Target chunk size in tokens |
| `EKIE_CHUNKING__MAX_TOKEN_BUDGET` | `1024` | Maximum chunk size in tokens |
| `EKIE_CHUNKING__MIN_CHUNK_TOKENS` | `8` | Minimum chunk size (drop below this) |
| `EKIE_CHUNKING__PRESERVE_TABLES` | `true` | Keep tables as atomic chunks |
| `EKIE_CHUNKING__PRESERVE_CODE` | `true` | Keep code blocks as atomic chunks |
| `EKIE_CHUNKING__RESPECT_SECTION_BOUNDARIES` | `true` | Do not split across section headings |
| `EKIE_CHUNKING__INCLUDE_BREADCRUMB_CONTEXT` | `true` | Prepend heading hierarchy to chunks |
| `EKIE_CHUNKING__RECURSIVE_CHUNK_SIZE` | `1000` | Character window for the `recursive` strategy (opt-in) |
| `EKIE_CHUNKING__RECURSIVE_CHUNK_OVERLAP` | `200` | Character overlap for the `recursive` strategy (must be < size) |

> **Recursive chunking (opt-in).** Set `EKIE_CHUNKING__DEFAULT_STRATEGY=recursive` to use LangChain's `RecursiveCharacterTextSplitter` (character window + overlap) instead of the structure-aware semantic splitter. It splits within each section, preserving section id/title/breadcrumb metadata. Requires `pip install langchain-text-splitters`. Semantic remains the default.

#### Embedding Framework

| Variable | Default | Description |
|---|---|---|
| `EKIE_EMBEDDING__PROVIDER` | `huggingface` | Allowed values: `local`, `ollama`, or `huggingface` |
| `EKIE_EMBEDDING__DEFAULT_MODEL` | `BAAI/bge-base-en-v1.5` | Active model — text embedding model |
| `EKIE_EMBEDDING__DIMENSION` | `768` | Output dimension of BAAI/bge-base-en-v1.5 |
| `EKIE_EMBEDDING__DISTANCE_METRIC` | `cosine` | Allowed values: `cosine`, `dot_product`, or `euclidean` |
| `EKIE_EMBEDDING__MAX_INPUT_TOKENS` | `512` | Maximum input token limit (bge-base context window) |
| `EKIE_EMBEDDING__BATCH_SIZE` | `16` | Chunks per embedding request. Raise (e.g. 32-64) for higher throughput on large document sets; it does not change the vectors |
| `EKIE_EMBEDDING__NORMALIZE_VECTORS` | `true` | L2-normalize output vectors |
| `EKIE_EMBEDDING__MAX_RETRIES` | `3` | Retry count on provider failures |
| `EKIE_EMBEDDING__MAX_REQUESTS_PER_MINUTE` | `0` | Optional throughput cap on embedding requests per minute (0 = unlimited) |
| `EKIE_EMBEDDING__OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |

> **Note on using HuggingFace locally:** The active embedding model is `BAAI/bge-base-en-v1.5` (dim=768). Required packages: `pip install -U sentence-transformers langchain-huggingface`. Model weights (~500 MB) are cached in `HF_HOME=./storage/hf`. To switch models, update `EKIE_EMBEDDING__DEFAULT_MODEL` and `EKIE_EMBEDDING__DIMENSION` in `.env` then restart.

> **GPU acceleration:** The default `torch` from PyPI is **CPU-only**. For an NVIDIA GPU, install a CUDA build matching your driver, e.g. (CUDA 13): `pip install --force-reinstall "torch==2.12.1" --index-url https://download.pytorch.org/whl/cu130` (verify with `python -c "import torch; print(torch.cuda.is_available())"`). Set `EKIE_EMBEDDING__DEVICE=auto` and `EKIE_EMBEDDING__TORCH_DTYPE=float16` — bge-base is small (~250 MB VRAM during ingest). The EKRE query embedder + reranker run on CPU so the EKCP chat LLM keeps the full 6 GB GPU. Restart the ingest worker (or API) for it to take effect.

The embedding dimension must be a plain integer (for example `768`), not a comma-formatted value.

#### Vector Publishing

| Variable | Default | Description |
|---|---|---|
| `EKIE_PUBLISHING__PROVIDER` | `local` | `local` (in-memory) or `qdrant` |
| `EKIE_PUBLISHING__DEFAULT_COLLECTION` | `enterprise_documents` | Target collection name |
| `EKIE_PUBLISHING__COLLECTION_STRATEGY` | `static` | `static` or `model_scoped` |
| `EKIE_PUBLISHING__BATCH_SIZE` | `64` | Vectors per upsert to the vector DB. Raise (e.g. 128-256) for faster ingest |
| `EKIE_PUBLISHING__MAX_RETRIES` | `3` | Retry count on publish failures |
| `EKIE_PUBLISHING__MAX_VECTORS_PER_MINUTE` | `0` | Optional throughput cap on vectors upserted per minute (0 = unlimited) |
| `EKIE_PUBLISHING__CREATE_MISSING_COLLECTIONS` | `true` | Auto-create collections |
| `EKIE_PUBLISHING__VERIFY_AFTER_PUBLISH` | `true` | Verify vectors after publish |

Collection strategy guidance:
1. `static`: always publish to `EKIE_PUBLISHING__DEFAULT_COLLECTION`.
2. `model_scoped`: publishes to a derived collection name including provider, model, and dimension suffix. Recommended when you switch embedding models frequently.

### 6.4 Orchestration Settings

| Variable | Default | Description |
|---|---|---|
| `EKIE_ORCHESTRATION__RUNNER` | `langgraph` | `sequential` or `langgraph` (active: langgraph for tracing) |
| `EKIE_ORCHESTRATION__MAX_ATTEMPTS_PER_STAGE` | `3` | Max retries per pipeline stage |
| `EKIE_ORCHESTRATION__RETRY_BACKOFF_BASE_SECONDS` | `0.0` | Backoff base (0 = no sleep) |
| `EKIE_ORCHESTRATION__RETRY_BACKOFF_MULTIPLIER` | `2.0` | Exponential backoff multiplier |
| `EKIE_ORCHESTRATION__ENABLE_TRACING` | `true` | Emit Langfuse traces (active) |

### 6.5 Security & Governance Settings

| Variable | Default | Description |
|---|---|---|
| `EKIE_SECURITY__REQUIRE_AUTHENTICATION` | `false` | Require API-key auth (local = off) |
| `EKIE_SECURITY__ENFORCE_AUTHORIZATION` | `true` | Enable RBAC + ABAC checks |
| `EKIE_SECURITY__ANONYMOUS_ROLE` | `service_worker` | Role for anonymous principal |
| `EKIE_SECURITY__ANONYMOUS_CLEARANCE` | `restricted` | Clearance for anonymous principal |
| `EKIE_SECURITY__MINIMUM_CLEARANCE` | `public` | Minimum resource classification |
| `EKIE_GOVERNANCE__ENABLE_AUDIT` | `true` | Enable audit trail |
| `EKIE_GOVERNANCE__AUDIT_SINK` | `logging` | `logging` or `memory` |
| `EKIE_GOVERNANCE__ALLOW_CLASSIFICATION_DOWNGRADE` | `false` | Permit classification lowering |

### 6.6 Plugin Settings

| Variable | Default | Description |
|---|---|---|
| `EKIE_PLUGINS__REQUIRE_SIGNATURE` | `true` | Require signed plugin manifests |
| `EKIE_PLUGINS__ALLOW_UNSIGNED` | `false` | Allow unsigned plugins (dev only) |
| `EKIE_PLUGINS__TRUSTED_PUBLISHERS` | *(empty)* | Comma-separated trusted publishers |
| `EKIE_PLUGINS__EKIE_VERSION` | `1.0.0` | Host version for compatibility |
| `EKIE_PLUGINS__SANDBOX_TIMEOUT_SECONDS` | `5.0` | Plugin execution timeout |

### 6.7 Deployment & DR Settings

| Variable | Default | Description |
|---|---|---|
| `EKIE_DEPLOYMENT__MIN_SUCCESS_RATE` | `0.99` | Pipeline success rate target |
| `EKIE_DEPLOYMENT__MAX_STAGE_LATENCY_SECONDS` | `5.0` | p95 per-stage latency budget |
| `EKIE_DEPLOYMENT__RPO_SECONDS` | `300.0` | Recovery Point Objective (5 min) |
| `EKIE_DEPLOYMENT__RTO_SECONDS` | `900.0` | Recovery Time Objective (15 min) |
| `EKIE_DEPLOYMENT__REPLICAS` | `1` | Desired replica count |

---

## 7. Infrastructure Setup

### 7.1 Start Local Infrastructure Stack

Before starting the infrastructure, ensure you have created a root `.env` file to provide credentials for the Docker containers. You can copy the template:
```bash
# On Windows PowerShell
Copy-Item .env.example .env
# On Mac/Linux
cp .env.example .env
```
Ensure you set required credentials (like `MINIO_ROOT_PASSWORD`) in this root `.env` file. SQL Server uses your Windows-native instance — no Docker MSSQL credentials needed.

The project provides a Docker Compose file that starts all required services:

```bash
docker compose -f docker-compose.local.yml up -d
```

This starts the following services:

| Service | Port | Purpose |
|---|---|---|
| **Qdrant** | `6333` | Vector database |
| **Redis 7** | `6379` | Cache layer |
| **MinIO** | `9005` (API), `9006` (Console) | Object storage |
| **Langfuse** | `3000` | Observability (LLM tracing) |
| **ClickHouse** | `8123` | Langfuse internal analytics |
| **PostgreSQL 16** | *(internal)* | Langfuse internal store only |

> **SQL Server** is your **Windows-native instance** (`localhost\MSSQLSERVER2022`). It is NOT in Docker. EKIE connects via Windows Authentication.
> **Note on Qdrant:** Qdrant stores its data in a managed Docker volume.
> **MinIO ports:** MinIO API runs on host port **9005** (mapped to container port 9000). Console runs on host port **9006**. These are fixed in `docker-compose.local.yml` to avoid conflicts with Windows reserved ports.

### 7.2 Verify Services

```bash
# Check all containers are running
docker compose -f docker-compose.local.yml ps

# Verify Qdrant
curl http://localhost:6333/healthz

# Verify MinIO
curl http://localhost:9005/minio/health/live

# Verify MS SQL Server connectivity
# (requires sqlcmd or equivalent client)

# Option 1: SQL Server Authentication (Docker container)
sqlcmd -S localhost,1433 -U sa -P "YourPassword" -Q "SELECT 1"

# Option 2: Windows Authentication (Local Native Instance with ODBC 18)
# Note: Do not append ',1433' when specifying a named instance. Use the -C flag to trust the self-signed certificate.
sqlcmd -S "localhost\MSSQLSERVER2022" -E -C -Q "SELECT 1"
```

### 7.3 Create the Control Plane Database

Connect to MS SQL Server and create the database:

```sql
CREATE DATABASE ekrag_control_plane;
GO
```

> **Note:** When `EKIE_ENVIRONMENT=local`, the application auto-provisions the schema on startup via `db.create_all()`. No manual table creation is needed.

### 7.4 Create MinIO Bucket

Access the MinIO Console at `http://localhost:9006` and manually create a bucket named `ekie-assets`.

*(Optional)* If you have the [MinIO Client (mc)](https://min.io/docs/minio/linux/reference/minio-mc.html) installed on your machine, you can do this via the command line instead:
```bash
mc alias set local http://localhost:9005 minioadmin minioadmin
mc mb local/ekie-assets
```

### 7.5 Install HuggingFace Model Dependencies (Required)

The active configuration uses HuggingFace for both embedding and intelligence. Install the required packages:

```powershell
# Text embedding model dependencies (bge-base; no image extras needed)
pip install -U sentence-transformers

# Intelligence LLM dependencies
pip install langchain-huggingface torch transformers accelerate
```

On first ingest:
1. `BAAI/bge-base-en-v1.5` (~500 MB) downloads to `./storage/hf`.
2. `Qwen/Qwen2.5-3B-Instruct` (~3 GB) downloads on first document with high complexity (only when `ENABLE_LLM_ANALYSIS=true`).
3. After download, set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` for strict offline operation.

### 7.6 Optional: Use Ollama Instead of HuggingFace

To switch to Ollama for embeddings and/or intelligence, apply the Ollama profile:

```powershell
Copy-Item services/ekie/.env.profile.ollama services/ekie/.env -Force
```

Then pull the required models:
```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

---

## 8. Running the Service

### 8.1 Start the EKIE API Server

```powershell
# Recommended: cwd-safe launcher (works from any directory)
python services/ekie/scripts/start_api.py

# Or use the entry-point shortcut after pip install -e services/ekie[...]:
ekie-api

# Manual (must run from services/ekie/ for .env to load):
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -m uvicorn api.app:app --host 0.0.0.0 --port 8001 --app-dir src
```

The API host and port are controlled by the `EKIE_GATEWAY__HOST` and `EKIE_GATEWAY__PORT` environment variables (defaults: `0.0.0.0` and `8001`).

### 8.2 Verify the Service

```bash
# Liveness probe
curl http://localhost:8001/health/live
# Response: {"status": "ok", "service": "ekie"}

# Readiness probe
curl http://localhost:8001/health/ready
# Response: {"status": "ready", "service": "ekie"}

# OpenAPI docs
# Open in browser: http://localhost:8001/docs
```

### 8.3 Run in Offline Mode (No Infrastructure)

EKIE supports a fully offline mode using the local providers and an in-memory SQLite database. This is the default configuration and requires zero external services:

```dotenv
# .env overrides for offline operation (these are the defaults)
EKIE_CONTROL_PLANE__URL=sqlite+pysqlite:///:memory:
EKIE_EMBEDDING__PROVIDER=local
EKIE_PUBLISHING__PROVIDER=local
```

### 8.4 Async Ingestion, Live Monitor & Job Management

When `EKIE_INGESTION__ASYNC_ENABLED=true`, the API returns `202 Accepted` and a
durable worker pool runs the pipeline out of the request path. Start the worker
alongside the API:

```powershell
python services/ekie/scripts/start_ingest_worker.py   # or: ekie-ingest-worker
```

**Restart safety.** Stage payloads persist to disk (`EKIE_STORAGE__LOCAL_PATH`,
default `storage/assets`), and a live worker heartbeats its job lock every
`EKIE_INGESTION__HEARTBEAT_INTERVAL_SECONDS` (15s). If a worker is hard-killed,
its job is reclaimed and **resumed** once the lock is stale
(`EKIE_INGESTION__VISIBILITY_TIMEOUT_SECONDS`, ~90s); stopping with **Ctrl+C**
releases the job immediately. Resume is stage-granular: a job interrupted mid-way
re-runs from the first incomplete stage.

**Live monitor.** Watch per-document progress with:

```powershell
python services/ekie/scripts/monitor.py   # or: ekie-monitor
```

The Status column shows:

| Status | Meaning |
|--------|---------|
| `>> E 128/260 49%` / `>> P 0/258` | **Running now**, with live per-batch progress for embedding/publishing. |
| `waiting · resume E [next / #N in line]` | Partially done and **queued to resume**; the bracket is its position in the worker's claim order (`[…, in 40s]` = retry backoff still counting down). |
| `queued [#N in line]` | Not started; bracket shows queue position. |
| `complete` / `dead-letter xN` | Finished / retries exhausted. |

Navigate with **↑/↓**, **PgUp/PgDn**, **Home/End**, **f** (toggle FOLLOW/SCROLL),
and **q** or **Ctrl+C** to quit. With a single worker (`WORKER_CONCURRENCY=1`),
documents process one at a time; the queue position tells you when each resumes.

**Requeue a dead-letter job** after fixing its cause (the orchestrator resumes
from the first incomplete stage):

```powershell
python services/ekie/scripts/requeue_jobs.py --list
python services/ekie/scripts/requeue_jobs.py --job-id <id>       # or --document-id <id> / --all-dead
```

**Remove a document** (hard delete — purges vectors, assets, lineage, jobs, and
staged source):

```powershell
python services/ekie/scripts/purge_documents.py --list
python services/ekie/scripts/purge_documents.py --document-id <id> --yes
python services/ekie/scripts/purge_documents.py --source-path "Report.pdf.md" --yes
```

**Recover payload-lost documents** (only needed after upgrading from an older
in-memory build; resets stale stage rows and re-ingests from the stored source):

```powershell
python services/ekie/scripts/recover_lost_payload_docs.py
```

---

## 9. API Reference

### 9.1 Base URL

```
http://localhost:8001
```

### 9.2 Required Headers

Every request must include:

| Header | Required | Description |
|---|---|---|
| `X-Tenant-ID` | **Yes** | Tenant identifier for multi-tenant isolation |
| `X-Correlation-ID` | No | Correlation ID for tracing (auto-generated if absent) |

### 9.3 Endpoints

#### Health Endpoints

```
GET /health/live
```

Returns liveness status. Response:
```json
{"status": "ok", "service": "ekie"}
```

---

```
GET /health/ready
```

Returns readiness status. Response:
```json
{"status": "ready", "service": "ekie"}
```

#### Ingestion Endpoints

```
POST /v1/documents/{document_id}/ingest
```

Run the full ingestion workflow for a synced document. The document bytes are sent in the request body. EKIE expects Markdown (or plain text) — non-Markdown source files are converted to Markdown upstream by the EKDC agent before ingestion.

**Parameters:**
- `document_id` (path, required): The document ID from the Control Plane
- `sync` (query, optional, default false): When async ingestion is enabled, set `sync=true` to force inline execution and receive the full `WorkflowResponse` instead of a `202` acknowledgement. Ignored when async is disabled.
- `mime_type` (query, optional): MIME type hint (e.g., `text/markdown`, `text/plain`)
- `intelligence_provider` (query, optional): Override the LLM provider for document analysis (e.g., `huggingface` or `ollama`).
- `intelligence_model` (query, optional): Override the LLM model used for analysis (e.g., `meta-llama/Llama-3-8b-chat-hf`).
- `embedding_provider` (query, optional): Override the embedding provider (e.g., `huggingface` or `ollama`).
- `embedding_model` (query, optional): Override the embedding model used for vector generation.

**Synchronous vs. asynchronous:** When `EKIE_INGESTION__ASYNC_ENABLED=false` (default) the pipeline runs inline and returns `200 OK` with the completed `WorkflowResponse`. When async is enabled the API persists the source, enqueues a durable job, and returns `202 Accepted`; a running ingest worker (`scripts/start_ingest_worker.py`) then executes the pipeline. Track progress via `GET /v1/documents/{document_id}/job`.

**Request:**
```bash
# Example: Basic Ingestion
curl -X POST "http://localhost:8001/v1/documents/doc-123/ingest?mime_type=text/markdown" \
  -H "X-Tenant-ID: tenant-1" \
  -H "X-Correlation-ID: corr-abc" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @document.md

# Example: Dynamic Model Selection (HuggingFace)
curl -X POST "http://localhost:8001/v1/documents/doc-124/ingest?intelligence_provider=huggingface&intelligence_model=meta-llama/Llama-3-8b-chat-hf&embedding_provider=huggingface&embedding_model=sentence-transformers/all-MiniLM-L6-v2" \
  -H "X-Tenant-ID: tenant-1" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @document.md
```

**Response (200 OK):**
```json
{
  "document_id": "doc-123",
  "tenant_id": "tenant-1",
  "correlation_id": "corr-abc",
  "status": "completed",
  "completed_stages": ["transformation", "intelligence", "chunking", "embedding", "publishing"],
  "records": [
    {
      "stage": "transformation",
      "version": 1,
      "created": true,
      "content_hash": "sha256:abc123...",
      "attempts": 1
    }
  ],
  "failure": null
}
```

**Response (422 Unprocessable Content):**
Returned when the workflow is dead-lettered (all retry attempts exhausted):
```json
{
  "document_id": "doc-123",
  "status": "dead_letter",
  "failure": {
    "stage": "transformation",
    "error_type": "transformation_failed",
    "message": "Parser not found for format",
    "attempts": 3
  }
}
```

**Response (202 Accepted):**
Returned when async ingestion is enabled. The pipeline runs later in a worker:
```json
{
  "job_id": "b1f2...",
  "document_id": "doc-123",
  "tenant_id": "tenant-1",
  "kind": "ingest",
  "status": "queued",
  "status_url": "/v1/documents/doc-123/job",
  "message": "ingestion job enqueued"
}
```

---

```
GET /v1/documents/{document_id}/job
```

Return the latest durable ingestion job for a document (async path). Useful for
polling after a `202 Accepted` ingest response.

**Parameters:**
- `document_id` (path, required): Document ID from the Control Plane.

**Response (200 OK):**
```json
{
  "job_id": "b1f2...",
  "document_id": "doc-123",
  "tenant_id": "tenant-1",
  "kind": "ingest",
  "status": "running",
  "attempts": 1,
  "max_attempts": 3,
  "source_path": null,
  "last_error": null
}
```

Job `status` is one of `queued`, `running`, `succeeded`, `failed` (retrying), or
`dead_letter` (retries exhausted). Returns `404 Not Found` when no job exists for
the document.

---

```
POST /v1/documents/{document_id}/replay
```

Resume or replay a workflow from its last checkpoint or Control Plane lineage. If no source bytes are provided in the body, the pipeline attempts to resume from stored state.

**Parameters:**
- `document_id` (path, required): The document ID from the Control Plane
- `intelligence_provider` (query, optional): Override the LLM provider for analysis.
- `intelligence_model` (query, optional): Override the LLM model for analysis.
- `embedding_provider` (query, optional): Override the embedding provider.
- `embedding_model` (query, optional): Override the embedding model.

**Request:**
```bash
# Example: Replay with dynamic models
curl -X POST "http://localhost:8001/v1/documents/doc-123/replay?embedding_provider=ollama&embedding_model=nomic-embed-text" \
  -H "X-Tenant-ID: tenant-1"
```

---

```
DELETE /v1/documents/{document_id}
```

Hard-delete a document. Purges its published vectors from the vector database,
then removes the document's Control Plane rows. Deleting the document cascades to
its assets, workflows, and processing-state records. This is the delete path the
sync worker uses when a source file is removed.

**Parameters:**
- `document_id` (path, required): Document ID from the Control Plane.
- `force` (query, optional, default false): When false, a vector-cleanup failure
  aborts the delete so it can be retried safely. When true, the document rows are
  removed regardless and any cleanup error is reported in the response.

**Request:**
```bash
curl -X DELETE "http://localhost:8001/v1/documents/doc-123?force=false" \
  -H "X-Tenant-ID: tenant-1"
```

**Response (200 OK):**
```json
{
  "document_id": "doc-123",
  "tenant_id": "tenant-1",
  "vectors_deleted": 12,
  "row_deleted": true,
  "provider": "qdrant",
  "collection": "enterprise_documents",
  "vector_cleanup_error": null,
  "message": "document deleted"
}
```

Returns `404 Not Found` when no matching document exists for the tenant. For bulk
or orphaned-document cleanup (for example after the sync target directory is
changed), use `python services/ekie/scripts/purge_documents.py` (see its `--help`).

---

```
POST /v1/repositories/{repository_id}/ingest
```

Synchronize a repository and ingest its active documents in one call.

**Parameters:**
- `repository_id` (path, required): Repository ID from the Control Plane.
- `sync_before_ingest` (body, optional, default true): Run repository sync before ingestion.
- `document_ids` (body, optional): Restrict processing to listed document IDs.
- `max_documents` (body, optional): Limit number of documents processed.
- `intelligence_provider`, `intelligence_model`, `embedding_provider`, `embedding_model` (query, optional): Per-request provider/model overrides.

**Request:**
```bash
curl -X POST "http://localhost:8001/v1/repositories/repo-123/ingest" \
  -H "X-Tenant-ID: tenant-1" \
  -H "Content-Type: application/json" \
  -d '{"sync_before_ingest": true, "max_documents": 100}'
```

**Response summary fields:**
- `attempted`
- `completed`
- `dead_lettered`
- `results[]` with per-document workflow outcomes
- `errors[]` with per-document processing/read errors

---

```
GET /v1/documents/{document_id}/workflow
```

Return the reconciled workflow status inferred from Control Plane lineage records.

**Request:**
```bash
curl "http://localhost:8001/v1/documents/doc-123/workflow" \
  -H "X-Tenant-ID: tenant-1"
```

**Response:**
```json
{
  "document_id": "doc-123",
  "tenant_id": "tenant-1",
  "correlation_id": "...",
  "status": "completed",
  "completed_stages": ["transformation", "intelligence", "chunking", "embedding", "publishing"],
  "records": [...],
  "failure": null
}
```

---

## 10. Ingestion Pipeline Stages

The ingestion pipeline consists of five sequential stages, orchestrated by the Workflow Orchestrator:

### 10.1 Stage 1 — Transformation

**Module:** `domain/transformation/`
**Handbook Chapter:** 7

Converts incoming Markdown into the canonical Markdown asset. Conversion of
non-Markdown formats is owned by the upstream EKDC agent, so this stage does not
parse binary formats.

**How it works:**
1. The Markdown (or plain-text) bytes are decoded and read by the `ParserRegistry`.
2. The content is normalized (Unicode normalization, blank line collapsing).
3. A `MarkdownDocument` is produced with YAML front matter containing source metadata.
4. The document passes `MarkdownValidator` checks.
5. The Markdown and its content hash are stored as an immutable asset in the Control Plane.

**Supported Formats:**

| Format | Parser | Extensions |
|---|---|---|
| Markdown | `MarkdownParser` | `.md`, `.markdown` |
| Plain text | `PlainTextParser` | `.txt`, `.text`, `.log`, `.rtf` |

> All other formats (PDF, DOCX, PPTX, HTML, CSV, images, audio, video) are
> converted to Markdown upstream by the EKDC agent (`services/ekdc`) before they
> reach EKIE. EKIE no longer bundles OCR or rich-media extraction libraries.

**Configuration:** See [Section 6.3 — Document Transformation](#document-transformation).

### 10.2 Stage 2 — Intelligence

**Module:** `domain/intelligence/`
**Handbook Chapter:** 8

Analyzes the canonical Markdown to extract rich metadata and quality signals.

**Analyzer Pipeline:**
1. **StructureAnalyzer** — Parses the Markdown AST into a section tree with heading hierarchy, depth, and content statistics.
2. **LanguageAnalyzer** — Detects the document language using heuristic analysis.
3. **ClassificationAnalyzer** — Classifies the document category (procedure, policy, reference, tutorial, report, technical, general).
4. **QualityAnalyzer** — Scores document quality (heading coverage, section balance, metadata completeness).
5. **SensitiveContentAnalyzer** — Detects sensitive content patterns (PII, credentials, financial data, health information).
6. **TableAnalyzer** — Extracts table statistics (count, dimensions, headers).
7. **FigureAnalyzer** — Identifies figure/image references and captions.
8. **CodeAnalyzer** — Detects code blocks with language identification.
9. **LlmAnalyzer** *(active when `ENABLE_LLM_ANALYSIS=true`)* — Uses a local HuggingFace model (`Qwen/Qwen2.5-3B-Instruct`) for advanced topic extraction and summarization.

**Output:** A `DocumentIntelligenceReport` containing:
- Semantic metadata (title, description, topics, author)
- Document category and complexity rating
- Section intelligence with per-section analysis
- Quality score
- Sensitive content findings
- Table, figure, and code block inventories

### 10.3 Stage 3 — Chunking

**Module:** `domain/chunking/`
**Handbook Chapter:** 9

Splits the canonical Markdown into semantically meaningful chunks optimized for retrieval.

**Chunking Strategies:**

| Strategy | Description |
|---|---|
| `semantic` | **(Default)** Respects heading hierarchy, section boundaries, and content structure |
| `section_based` | One chunk per top-level section |
| `heading_based` | Splits at heading boundaries |
| `paragraph_based` | Splits at paragraph boundaries |
| `token_based` | Fixed token-window with overlap |
| `table_based` | Preserves tables as atomic chunks |
| `code_based` | Preserves code blocks as atomic chunks |
| `recursive` | **(Opt-in)** LangChain `RecursiveCharacterTextSplitter`: character window + overlap, split within each section (preserves section metadata). Requires `langchain-text-splitters` |

**Features:**
- **Breadcrumb context**: Each chunk is prepended with its heading hierarchy path (e.g., `# Document > ## Section > ### Subsection`), providing retrieval context.
- **Table and code preservation**: Tables and code blocks are never split mid-structure.
- **Token budget enforcement**: Chunks respect configurable minimum, target, and maximum token budgets.
- **Validation**: A `ChunkValidator` verifies chunk integrity, overlap consistency, and coverage.

### 10.4 Stage 4 — Embedding

**Module:** `domain/embedding/`
**Handbook Chapter:** 10

Generates vector embeddings from chunk text.

**Providers:**

| Provider | Configuration | Description |
|---|---|---|
| `local` | `EKIE_EMBEDDING__PROVIDER=local` | Deterministic SHA-256 hash-based embeddings. Zero dependencies, fully offline. Produces reproducible vectors for testing and development. |
| `huggingface` | `EKIE_EMBEDDING__PROVIDER=huggingface` | Real neural embeddings via a local HuggingFace model. **Active default.** Current model: `BAAI/bge-base-en-v1.5` (dim=768). Requires `sentence-transformers` only. |
| `ollama` | `EKIE_EMBEDDING__PROVIDER=ollama` | Real neural embeddings via a locally-hosted Ollama model. Recommended models: `nomic-embed-text` (768d), `mxbai-embed-large` (1024d). |

**Features:**
- **Model registry**: Validates model compatibility and tracks model specifications.
- **Batch processing**: Chunks are embedded in configurable batches.
- **Cost estimation**: Tracks estimated token costs per embedding operation.
- **Retry with backoff**: Provider failures trigger exponential backoff retries.
- **Optional rate limiting**: `EKIE_EMBEDDING__MAX_REQUESTS_PER_MINUTE` paces embedding requests per minute (0 = unlimited) to respect a throttled provider.
- **Vector validation**: Verifies dimensionality, normalization, and numeric integrity.

### 10.5 Stage 5 — Publishing

**Module:** `domain/publishing/`
**Handbook Chapter:** 11

Publishes embedding vectors to the vector database with enforced metadata.

**Providers:**

| Provider | Configuration | Description |
|---|---|---|
| `local` | `EKIE_PUBLISHING__PROVIDER=local` | In-memory vector store for testing and development. |
| `qdrant` | `EKIE_PUBLISHING__PROVIDER=qdrant` | Self-hosted Qdrant instance for production workloads. |

**Mandatory Metadata Fields:**

Every published vector must carry these metadata fields (enforced by the engine):

| Field | Source |
|---|---|
| `document_id` | Control Plane document record |
| `chunk_id` | Generated chunk identifier |
| `tenant_id` | Request tenant header |
| `classification_clearance` | Document classification |
| `distance_metric` | Embedding policy configuration |
| `source_path` | Original document path |
| `content_hash` | Document content hash |
| `version` | Asset version number |

**Features:**
- **Collection resolution**: Maps documents to collections via configurable policy.
- **Auto-creation**: Creates missing Qdrant collections with correct vector dimensions and distance metric.
- **Batch upsert**: Vectors are published in configurable batches.
- **Optional rate limiting**: `EKIE_PUBLISHING__MAX_VECTORS_PER_MINUTE` paces vector upserts per minute (0 = unlimited) to protect the vector DB.
- **Post-publish verification**: Verifies that all vectors are present and metadata is complete after publishing.
- **Idempotent**: Re-publishing the same content produces the same vector IDs.

---

## 11. Domain Modules Deep Dive

### 11.1 Repository Synchronization (`domain/sync/`)

Manages the Digital Twin model for enterprise repositories.

**Key Components:**
- `RepositorySynchronizer`: Orchestrates full and incremental sync cycles.
- `ChangeDetector`: Compares connector inventory against the Digital Twin to detect creates, modifies, renames, and deletes.
- `RepositoryConnector` (protocol): Abstraction for source repository access. Ships with `LocalFileSystemConnector`.
- `ConnectorRegistry`: Plugin registry for repository connectors.
- `SyncPolicy`: Environment-backed synchronization rules.
- State machines enforce valid lifecycle transitions for repositories and documents.

**Registration:**
```python
from domain.sync import register_repository

repository_id = register_repository(
    db,
    tenant_id="tenant-1",
    name="engineering-docs",
    source_type="local_fs",
    uri="/data/engineering",
)
```

### 11.2 Control Plane (`domain/control_plane/`)

The SQL Server-backed metadata registry and source of truth.

**ORM Models:**
- `Repository` — Registered source repositories
- `Document` — Document Digital Twins with version tracking
- `Asset` — Immutable versioned assets (markdown, intelligence, chunks, embeddings, vectors)
- `Lineage` — Parent-child lineage edges between assets
- `Workflow` — Ingestion workflow execution records
- `ProcessingState` — Per-stage status with retry counts

**Usage:**
```python
from domain.control_plane import ControlPlaneDatabase

db = ControlPlaneDatabase(settings.control_plane)
with db.session() as session:
    documents = session.query(Document).filter_by(tenant_id="tenant-1").all()
```

### 11.3 Asset Storage (`domain/storage/`)

Abstraction for immutable, versioned asset persistence.

- `AssetStorage` (protocol): Store and retrieve binary assets by key and version.
- `LocalFileAssetStorage`: **Default local-first backend.** Persists assets on disk under `EKIE_STORAGE__LOCAL_PATH` (default `storage/assets`), so stage payloads survive API/worker restarts.
- `InMemoryAssetStorage`: In-process store for tests and offline snippets. Data is lost on restart — not used by the running service in local mode.
- `MinIOAssetStorage`: Durable object storage backend using a self-hosted MinIO instance. Active when `EKIE_ENVIRONMENT` is not `local` and `EKIE_STORAGE__ENDPOINT` is non-empty.
- `compute_content_hash`: SHA-256 hash for content integrity.

Storage backend selection is automatic: the composition root calls `build_asset_storage(settings)` and returns the correct backend based on `EKIE_ENVIRONMENT`.

### 11.4 Workflow Orchestration (`domain/orchestration/`)

Executes the five-stage pipeline as a typed, checkpointed graph.

**Runners:**
- `SequentialWorkflowRunner`: Executes stages in order. Default offline runner.
- `LangGraphWorkflowRunner`: Builds a LangGraph `StateGraph` with checkpointing and Langfuse tracing.

**Features:**
- **Checkpointing**: Pipeline state is saved after each stage. A crash mid-pipeline resumes from the last checkpoint.
- **Dead-lettering**: When a stage exhausts its retry budget, the workflow is dead-lettered with a structured failure record.
- **Lineage-aware replay**: Even without a checkpoint, the orchestrator can reconstruct pipeline state from Control Plane lineage records.
- **Idempotent**: Re-running a completed workflow returns the cached result without re-processing.

**Composition:**
```python
from composition import build_workflow_orchestrator

orchestrator = build_workflow_orchestrator(settings, db, storage)
result = orchestrator.run(document_id, tenant_id, source_bytes=data, mime_type="text/markdown")
```

### 11.5 LangChain Resource Template (`domain/integrations/`)

A single, configuration-driven factory that initializes the embedding model and
the vector store from `.env`, so scripts and tools do not each construct
LangChain clients. It mirrors a standard RAG index (embedding model + vector
store) using LangChain building blocks.

**Factory functions** (`domain/integrations/langchain_resources.py`):
- `build_embeddings(provider, model, ...)`: returns a LangChain `Embeddings` for `huggingface` (local, offline-cached to `HF_HOME`) or `ollama`. The deterministic `local` provider is not a LangChain model and is rejected.
- `build_qdrant_vector_store(embeddings, *, collection, ...)`: returns a LangChain `QdrantVectorStore`. Connection precedence is `location` (e.g. `":memory:"`) > `url`/`api_key` > `host`/`port`; optionally creates the collection.
- `LangChainIndex`: bundles the embedding model with its vector store.

**Composition entry point:**
```python
from composition import build_langchain_index
from config.settings import EkieSettings

# Reads EKIE_EMBEDDING__* and EKIE_QDRANT__* from .env
index = build_langchain_index(EkieSettings(), create_collection=True)
index.vector_store.add_documents(docs)            # batched ingest
hits = index.vector_store.similarity_search(query)  # retrieval-ready
```

Requires `pip install langchain-qdrant` (plus `langchain-huggingface` or
`langchain-ollama`). This is a convenience/index seam: the production publishing
engine (Stage 5) keeps its own verified Qdrant client, metadata gate, and
post-publish verification and is unaffected by this template.

---

## 12. Security & Governance

### 12.1 Authentication

| Mode | Setting | Description |
|---|---|---|
| **Anonymous** (local default) | `REQUIRE_AUTHENTICATION=false` | An anonymous principal with configurable role and clearance is auto-created |
| **API Key** | `REQUIRE_AUTHENTICATION=true` | Requires a valid API key in the request |

### 12.2 Authorization (RBAC + ABAC)

EKIE enforces role-based access control combined with attribute-based security context:

**Roles and Permissions:**

| Role | Permissions |
|---|---|
| `admin` | All operations |
| `operator` | Manage workflows, read configuration |
| `service_worker` | Execute pipeline stages, read assets |
| `reader` | Read-only access to assets and status |

**Stage Policy Guard:**
Every pipeline stage is wrapped by a `StagePolicyGuard` that:
1. Verifies the principal's role has the required permission for the stage.
2. Validates the principal's clearance level against the document's classification.
3. Emits an audit record for the decision.

### 12.3 Classification Hierarchy

EKIE enforces a monotonic classification hierarchy:

```
public < internal < confidential < restricted < top_secret
```

- A derived asset always inherits the classification of its parent or higher.
- Classification downgrade is prohibited by default (`ALLOW_CLASSIFICATION_DOWNGRADE=false`).

### 12.4 Audit Trail

Every governed action emits an append-only `AuditRecord`:

```json
{
  "action": "stage_execute",
  "resource": "doc-123",
  "principal": "anonymous@service_worker",
  "result": "allowed",
  "tenant_id": "tenant-1",
  "correlation_id": "corr-abc",
  "timestamp": "2026-07-02T12:00:00Z"
}
```

**Audit Sinks:**
- `logging` — Structured JSON logs (default)
- `memory` — In-process store for testing

### 12.5 Secret Management

- Secrets are resolved via `EnvSecretProvider` from environment variables.
- All resolved secret values are registered with the `SecretRegistry`.
- A `RedactionFilter` is installed on the Python logger that scrubs any registered secret from log output.

---

## 13. Plugin SDK

### 13.1 Plugin Interface

Extend EKIE by implementing the `EKIEPlugin` protocol:

```python
from domain.plugins.sdk import EKIEPlugin, PluginContext

class MyCustomParser(EKIEPlugin):
    """A custom document parser plugin."""

    def execute(self, context: PluginContext) -> dict:
        # Plugin logic here
        return {"status": "ok", "result": ...}
```

### 13.2 Plugin Manifest

Every plugin requires a manifest describing its metadata and compatibility:

```python
from domain.plugins import PluginManifest, PluginType, SemVer

manifest = PluginManifest(
    name="my-custom-parser",
    version=SemVer(1, 0, 0),
    plugin_type=PluginType.PARSER,
    description="Custom Markdown enrichment parser",
    author="Engineering Team",
    min_ekie_version=SemVer(1, 0, 0),
    max_ekie_version=SemVer(2, 0, 0),
    signature="base64-encoded-signature...",
)
```

### 13.3 Plugin Registration and Activation

```python
from composition import build_plugin_registry

registry = build_plugin_registry(settings)
result = registry.register(manifest, MyCustomParser())

print(result.status)  # PluginStatus.ACTIVE or PluginStatus.REJECTED
```

**Activation Workflow:**
1. **Manifest validation** — Schema, required fields, publisher identity.
2. **Signature verification** — Unless `ALLOW_UNSIGNED=true` (development only).
3. **Version compatibility** — Semantic version range check against host version.
4. **Sandbox execution** — Plugin is test-executed in a sandboxed context with a configurable timeout.
5. **Registration** — Plugin is activated only after passing all validation checks.

### 13.4 Plugin Types

| Type | Extension Point |
|---|---|
| `PARSER` | Custom document format parsers |
| `ANALYZER` | Custom intelligence analyzers |
| `CHUNKER` | Custom chunking strategies |
| `EMBEDDER` | Custom embedding providers |
| `PUBLISHER` | Custom vector store providers |

---

## 14. Observability & Logging

### 14.1 Structured Logging

EKIE uses structured JSON logging with context-aware fields:

```json
{
  "timestamp": "2026-07-02T12:00:00.000Z",
  "level": "INFO",
  "logger": "ekie.orchestration",
  "message": "workflow_completed",
  "service": "ekie",
  "tenant_id": "tenant-1",
  "correlation_id": "corr-abc-123",
  "document_id": "doc-456",
  "duration_ms": 1234
}
```

**Key features:**
- Every log entry carries `tenant_id` and `correlation_id` from request context.
- The `JsonLogFormatter` produces machine-parseable JSON output.
- Secret redaction is automatic — any registered secret value is replaced with `[REDACTED]`.

### 14.2 Correlation Context

The `CorrelationMiddleware` binds per-request context:

- **X-Correlation-ID**: Auto-generated UUID if not provided. Returned in the response header.
- **X-Tenant-ID**: Required header for multi-tenant isolation.

Both values are thread-local and automatically included in all log entries and events.

### 14.3 Langfuse Integration

Langfuse 3.x requires **two containers** to trace ingestion workflows: the web app (`langfuse`) and the queue processor (`langfuse-worker`). Without the worker, traces are accepted with HTTP 207 but never appear in the UI.

Start the full stack:

```powershell
docker compose -f docker-compose.local.yml up -d clickhouse langfuse-db langfuse langfuse-worker
```

Required `.env` settings:

```dotenv
EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true
EKIE_OBSERVABILITY__LANGFUSE_URL=http://localhost:3000
EKIE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY=pk-lf-<from-langfuse-ui>
EKIE_OBSERVABILITY__LANGFUSE_SECRET_KEY=sk-lf-<from-langfuse-ui>
EKIE_ORCHESTRATION__RUNNER=langgraph
EKIE_ORCHESTRATION__ENABLE_TRACING=true
```

Get API keys: http://localhost:3000 → Settings → API Keys.

**Python SDK:** pin to `langfuse>=2.0,<3.0`. Version 4.x uses OTEL protocol which is incompatible with the self-hosted docker stack.

```powershell
pip install "langfuse>=2.0,<3.0"
```

Operational requirements:
1. `langfuse` and `langfuse-worker` containers both healthy before EKIE startup.
2. API keys from Langfuse UI set in `.env`.
3. EKIE API restarted after key change.

Verification:

```powershell
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -c "
import sys, requests, base64; sys.path.insert(0, 'src')
from config.settings import get_settings; s = get_settings()
creds = base64.b64encode(f'{s.observability.langfuse_public_key}:{s.observability.langfuse_secret_key}'.encode()).decode()
resp = requests.get('http://localhost:3000/api/public/traces?limit=5', headers={'Authorization': f'Basic {creds}'})
traces = resp.json().get('data', [])
print(f'Traces in Langfuse: {len(traces)}')
[print(' -', t.get('name'), t.get('id')) for t in traces]
"
Pop-Location
```

### 14.4 OpenTelemetry

Configure the OTEL exporter for distributed tracing:

```dotenv
EKIE_OBSERVABILITY__OTEL_EXPORTER_ENDPOINT=http://localhost:4317
```

### 14.5 Pipeline Events

Every pipeline stage emits typed domain events:

| Domain | Event Types |
|---|---|
| Sync | `sync_started`, `document_discovered`, `document_modified`, `sync_completed` |
| Transformation | `transformation_started`, `transformation_completed`, `transformation_failed` |
| Intelligence | `analysis_started`, `analysis_completed`, `analysis_failed` |
| Chunking | `chunking_started`, `chunking_completed`, `chunking_failed` |
| Embedding | `embedding_started`, `embedding_completed`, `embedding_failed` |
| Publishing | `publish_started`, `publish_completed`, `publish_verified`, `publish_failed` |
| Orchestration | `workflow_started`, `stage_started`, `stage_completed`, `stage_failed`, `workflow_completed`, `workflow_dead_lettered` |

---

## 15. Validation & Readiness

### 15.1 Pipeline Validation

The `PipelineValidator` verifies end-to-end pipeline correctness:

```python
from composition import build_pipeline_validator

validator = build_pipeline_validator(db, storage)
report = validator.validate(document_id, tenant_id)

for finding in report.findings:
    print(f"[{finding.severity.value}] {finding.message}")
```

**Validation checks:**
- **Workflow completeness**: All stages completed successfully.
- **Asset lineage**: Every derived asset has a valid parent chain back to the source document.
- **Chunk integrity**: Chunks cover the source content without gaps or invalid overlaps.
- **Embedding consistency**: Dimensionality, normalization, and model metadata match the policy.
- **Vector metadata**: All mandatory fields are present and correctly populated.

### 15.2 Load Testing

Run synthetic load against the pipeline:

```python
from domain.validation import DocumentLoadSpec, run_load

spec = DocumentLoadSpec(
    document_count=100,
    document_size_bytes=4096,
    concurrent_workers=4,
)
report = run_load(orchestrator, spec, tenant_id="tenant-load")
print(f"Success rate: {report.success_rate:.2%}")
print(f"p95 latency: {report.p95_latency_seconds:.2f}s")
```

### 15.3 EKRE Handoff Readiness

Before handoff to the downstream Retrieval Engine (EKRE), verify handoff readiness:

```python
from domain.validation import build_handoff_package, assess_readiness

package = build_handoff_package(db, storage, document_id, tenant_id)
readiness = assess_readiness(package, settings.deployment)
```

The readiness assessment checks:
- All pipeline stages completed.
- Vector metadata contains mandatory fields for EKRE consumption.
- Distance metric and embedding dimension are recorded for EKRE inheritance.
- Success rate meets the configured minimum (`EKIE_DEPLOYMENT__MIN_SUCCESS_RATE`).

### 15.4 Failure Injection

Test pipeline resilience by injecting controlled failures:

```python
from domain.validation import failing_stages, InjectedStageFailure

# Inject a failure at the chunking stage
failures = failing_stages(["chunking"])
```

---

## 16. Demo Scripts

EKIE ships with nine demo scripts in `services/ekie/scripts/` that demonstrate each subsystem end to end. All demos run fully offline with no external dependencies.

### 16.1 Running Demo Scripts

```bash
# From the repository root, with the virtual environment activated:

# Repository Synchronization
.venv/Scripts/python.exe services/ekie/scripts/demo_sync.py

# Document Transformation
.venv/Scripts/python.exe services/ekie/scripts/demo_transform.py

# Document Intelligence
.venv/Scripts/python.exe services/ekie/scripts/demo_intelligence.py

# Intelligent Chunking
.venv/Scripts/python.exe services/ekie/scripts/demo_chunking.py

# Embedding Generation
.venv/Scripts/python.exe services/ekie/scripts/demo_embedding.py

# Vector Publishing
.venv/Scripts/python.exe services/ekie/scripts/demo_publishing.py

# Full Workflow Orchestration (recommended first demo)
.venv/Scripts/python.exe services/ekie/scripts/demo_orchestration.py

# Security & Governance
.venv/Scripts/python.exe services/ekie/scripts/demo_security.py

# Pipeline Validation
.venv/Scripts/python.exe services/ekie/scripts/demo_validation.py
```

### 16.2 Orchestration Demo Walkthrough

The `demo_orchestration.py` script is the best starting point. It demonstrates:

1. **Full ingestion run** — Syncs a sample maintenance procedure document, then runs all five pipeline stages with per-stage records and lifecycle events.
2. **Idempotent replay** — Re-runs the same document, demonstrating that completed stages are not re-processed.
3. **Lineage-aware reconciliation** — Reconstructs pipeline state from Control Plane records without a checkpoint.
4. **Dead-lettering** — Attempts to process a document with no source content, demonstrating failure handling and dead-letter output.

---

## 17. Testing

### 17.1 Test Suite Overview

EKIE has 42 test files covering all domain modules:

| Test Area | Files | Coverage |
|---|---|---|
| Sync framework | `test_sync_*.py`, `test_connectors.py`, `test_change_detection.py` | Change detection, connectors, sync service |
| Transformation | `test_transformation_*.py` | Parsers, pipeline, markdown output |
| Intelligence | `test_intelligence_*.py` | Analyzers, AST, LLM integration |
| Chunking | `test_chunking_*.py` | Engine, strategies, validation |
| Embedding | `test_embedding_*.py` | Engine, providers, validation |
| Publishing | `test_publishing_*.py` | Engine, providers, metadata |
| Orchestration | `test_orchestration_*.py` | Engine, runner (sequential + LangGraph) |
| Security | `test_security.py`, `test_composition_security.py` | Auth, RBAC, audit, redaction |
| Plugins | `test_plugins.py` | Registry, sandbox, validation |
| Validation | `test_validation_*.py` | Pipeline, readiness, load, handoff |
| API | `test_health.py`, `test_ingestion_api.py` | HTTP endpoints |
| Config | `test_settings.py`, `test_composition.py` | Settings, composition root |

### 17.2 Running Tests

```bash
cd services/ekie

# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_orchestration_engine.py -v

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run type checking
python -m mypy src/ --strict
```

### 17.3 Test Configuration

Tests use an in-memory SQLite database and in-memory asset storage by default. No external infrastructure is required:

```python
# From conftest.py — test settings override
settings = EkieSettings()
db = ControlPlaneDatabase(ControlPlaneSettings(url="sqlite+pysqlite:///:memory:"))
db.create_all()
storage = InMemoryAssetStorage()
```

---

## 18. Deployment Guide

### 18.0 Zero-Code Model Switching Rule

Changing providers and models is a configuration operation:
1. Update values in `services/ekie/.env`.
2. Restart EKIE service.
3. Run health checks and a smoke ingest.

You should not modify `services/ekie/src/config/settings.py` for routine model changes.

### 18.1 Environment Profiles

| Environment | Key Settings |
|---|---|
| **Local (default)** | `ENVIRONMENT=local`, local providers, in-memory storage, auto-schema provision |
| **Staging** | `ENVIRONMENT=staging`, Qdrant + Ollama providers, MS SQL, MinIO |
| **Production** | `ENVIRONMENT=production`, full stack, authentication required, >=2 replicas |

### 18.1.1 Recommended profile files

Use the committed profile files under `services/ekie/` and copy one into `services/ekie/.env` during deployment:
1. `.env.profile.ollama`
2. `.env.profile.huggingface`
3. `.env.profile.hybrid`
4. `.env.profile.rollback-last-known-good`

PowerShell examples:
```powershell
Copy-Item services/ekie/.env.profile.hybrid services/ekie/.env -Force
Copy-Item services/ekie/.env.profile.rollback-last-known-good services/ekie/.env -Force
```

Hybrid profile example:
1. `EKIE_INTELLIGENCE__LLM_PROVIDER=huggingface`
2. `EKIE_INTELLIGENCE__LLM_MODEL=<hf-chat-model>`
3. `EKIE_EMBEDDING__PROVIDER=ollama`
4. `EKIE_EMBEDDING__DEFAULT_MODEL=nomic-embed-text:latest`
5. `EKIE_EMBEDDING__DIMENSION=768`
6. `EKIE_PUBLISHING__COLLECTION_STRATEGY=model_scoped`

### 18.2 Production Configuration Checklist

- [ ] `EKIE_SECURITY__REQUIRE_AUTHENTICATION=true`
- [ ] `EKIE_EMBEDDING__PROVIDER=huggingface` (active) or `ollama`
- [ ] `EKIE_EMBEDDING__DEFAULT_MODEL=BAAI/bge-base-en-v1.5` (active, dim=768)
- [ ] `EKIE_PUBLISHING__PROVIDER=qdrant`
- [ ] `EKIE_ENVIRONMENT=production` (activates MinIO durable storage)
- [ ] `EKIE_STORAGE__ACCESS_KEY` and `SECRET_KEY` set
- [ ] `EKIE_CONTROL_PLANE__TRUSTED_CONNECTION=true` (Windows Auth) or PASSWORD set
- [ ] `EKIE_GOVERNANCE__ENABLE_AUDIT=true`
- [ ] `EKIE_GOVERNANCE__AUDIT_SINK=logging`
- [ ] `EKIE_PLUGINS__ALLOW_UNSIGNED=false`
- [ ] `EKIE_PLUGINS__REQUIRE_SIGNATURE=true`
- [ ] `EKIE_DEPLOYMENT__REPLICAS=2` (or higher)
- [ ] `EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true` (active)
- [ ] `EKIE_ORCHESTRATION__ENABLE_TRACING=true` (active)

### 18.2.1 Model-switch checklist

- [ ] Provider values are valid (`ollama` or `huggingface` for intelligence; `local`, `ollama`, or `huggingface` for embedding)
- [ ] Embedding dimension matches selected model capability
- [ ] Publishing collection strategy chosen (`model_scoped` recommended for frequent model changes)
- [ ] Smoke ingest passes after restart
- [ ] Qdrant collection has points and payload metadata

### 18.2.2 End-to-end deployment steps (operator runbook)

1. Prepare environment files
   - Copy `services/ekie/.env.example` to `services/ekie/.env`.
   - Set database credentials, storage credentials, model-provider variables.
   - Add Langfuse API keys (get from UI after step 2).

2. Start infrastructure (run once; includes Langfuse worker)
```powershell
docker compose -f docker-compose.local.yml up -d
docker compose -f docker-compose.local.yml ps
# All services should show (healthy) or Up.
```

3. Create Langfuse account and copy API keys
   - Open http://localhost:3000, register, create project.
   - Settings → API Keys → copy `pk-lf-...` and `sk-lf-...` to `.env`.

4. Install Python dependencies (run once per machine)
```powershell
pip install -e "services/ekie[dev,mssql,storage]"
pip install -U sentence-transformers langchain-huggingface torch transformers accelerate "langfuse>=2.0,<3.0"
# The mssql extra installs pyodbc (required for the SQL Server control plane).
```

5. Download HuggingFace models (run once; ~500 MB embedding, +~3 GB if LLM analysis enabled)
```powershell
python services/ekie/scripts/setup.py
# Or manually:
Push-Location services/ekie
..\..\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-base-en-v1.5', ignore_patterns=['*.gguf','*.bin'])"
..\..\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-3B-Instruct', ignore_patterns=['*.gguf','*.bin'])"
Pop-Location
```

6. Set offline flags in `.env` after download completes
```dotenv
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

7. Start EKIE API (Terminal A)
```powershell
python services/ekie/scripts/start_api.py
```

8. Start ingestion worker (Terminal B)
```powershell
python services/ekie/scripts/start_worker.py
```

9. Run API health checks
```powershell
Invoke-RestMethod http://localhost:8001/health/live
Invoke-RestMethod http://localhost:8001/health/ready
```

10. Get repository ID and trigger first ingest
```powershell
$headers = @{ 'X-Tenant-ID' = 'tenant-default'; 'Content-Type' = 'application/json' }
Push-Location services/ekie; ..\..\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); from config.settings import get_settings; from domain.control_plane import ControlPlaneDatabase, Repository; db = ControlPlaneDatabase(get_settings().control_plane); [print(r.id, r.name) for r in __import__('sqlalchemy.orm', fromlist=['Session']).Session; db.session().__enter__().query(Repository).filter_by(tenant_id='tenant-default').all()]"
# Use ID from above:
Invoke-RestMethod -Method Post -Uri 'http://localhost:8001/v1/repositories/<repo-id>/ingest' -Headers $headers -Body '{"sync_before_ingest":true,"max_documents":5}' | ConvertTo-Json -Depth 5
```

11. Verify data in all monitoring layers
   - Qdrant: http://localhost:6333/dashboard
   - MinIO: http://localhost:9006 (minioadmin / minioadmin)
   - Langfuse: http://localhost:3000 → Traces

### 18.3 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY packages/contracts/ packages/contracts/
RUN pip install -e packages/contracts/

COPY services/ekie/ services/ekie/
RUN pip install -e "services/ekie[mssql]"

EXPOSE 8001
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8001", "--app-dir", "services/ekie/src"]
```

### 18.4 Health Checks

Configure container health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health/ready"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

---

## 19. Troubleshooting

### 19.1 Common Issues

#### Service fails to start with ODBC error

```
Error: Can't open lib 'ODBC Driver 18 for SQL Server'
```

**Solution:** Install the ODBC Driver 18 for SQL Server. See [Section 5.5](#55-install-odbc-driver-ms-sql-server).

**Quick workaround for local development:** Use the SQLite URL override:
```dotenv
EKIE_CONTROL_PLANE__URL=sqlite+pysqlite:///./ekie_local.db
```

#### Missing X-Tenant-ID header

```json
{"detail": "X-Tenant-ID header is required"}
```

**Solution:** Include the `X-Tenant-ID` header in every request:
```bash
curl -H "X-Tenant-ID: my-tenant" http://localhost:8001/v1/documents/...
```

#### Workflow dead-lettered at transformation stage

```json
{"failure": {"stage": "transformation", "error_type": "parser_not_found"}}
```

**Solution:** The document format is not supported by any registered parser. Check:
1. The file extension or MIME type is in the supported list.
2. A custom parser plugin is registered for the format.

#### Embedding dimension mismatch

```
EmbeddingValidationError: Expected dimension 768, got 256
```

**Solution:** Ensure `EKIE_EMBEDDING__DIMENSION` matches the actual output dimension of your embedding model. For example, `nomic-embed-text` outputs 768 dimensions. Use plain integers only (`768`, not `4,096`).

#### Large documents dead-letter at the embed stage (`token_limit_exceeded`)

**Symptom:** Small documents ingest fine, but larger ones dead-letter. `last_error`
(via `requeue_jobs.py --list`) reads similar to:

```
chunk 'CHK-000042' has 731 tokens; model 'BAAI/bge-base-en-v1.5' allows 512
```

**Cause:** A chunk is larger than the embedding model's context window. The chunker
may emit a chunk up to `EKIE_CHUNKING__MAX_TOKEN_BUDGET`, and preserved tables/code
blocks are exempt from that budget entirely — so a dense section, big table, or long
code block in a large document produces a chunk over `EKIE_EMBEDDING__MAX_INPUT_TOKENS`.
Small documents never contain such a chunk, so only the big ones fail. The budgets are
whitespace-word estimates, while models such as bge tokenize into sub-words (~1.3× more),
so a chunk near the limit can overflow even when the word count looks safe.

**Fix — choose one:**

1. **Truncate to fit (default, no dead-letters).** Set
   `EKIE_EMBEDDING__TRUNCATE_OVERSIZED_CHUNKS=true`. Oversized chunks are clipped to the
   model window and an `EmbeddingTruncated` warning event is emitted; the document always
   completes. Combine with a smaller `EKIE_CHUNKING__TARGET_TOKEN_BUDGET` (for bge-base's
   512-token window, `350` leaves headroom) so truncation almost never triggers.

2. **Size chunks so nothing is truncated (no code change).** Set
   `EKIE_EMBEDDING__TRUNCATE_OVERSIZED_CHUNKS=false` and size chunks below the model
   window. For guaranteed sub-window chunks — including large tables/code — use the
   character splitter:

   ```dotenv
   EKIE_EMBEDDING__MAX_INPUT_TOKENS=512          # match your model (bge-base = 512)
   EKIE_EMBEDDING__TRUNCATE_OVERSIZED_CHUNKS=false
   EKIE_CHUNKING__DEFAULT_STRATEGY=recursive     # splits within blocks; needs langchain-text-splitters
   EKIE_CHUNKING__RECURSIVE_CHUNK_SIZE=1500       # ~375 tokens; safely under 512
   EKIE_CHUNKING__RECURSIVE_CHUNK_OVERLAP=200
   ```

   The `semantic` strategy keeps tables/code atomic and never sub-splits a single block,
   so with `truncate=false` a single oversized block will still dead-letter — use
   `recursive` (or keep `truncate=true`) if your documents contain large tables/code.

After editing `.env`, restart the API and the ingest worker so both load the new settings,
then re-ingest the affected documents (see **Re-ingesting after a fix**, below).

#### Re-ingesting after a fix

Re-embedding **every** document is not required. Documents that already completed were
embedded with their full content and stay valid — leave them. Only re-process the
documents that dead-lettered (they have no vectors yet), and only re-chunk when you
changed a chunking setting and want it applied.

1. **List what needs attention:**

   ```powershell
   python services/ekie/scripts/requeue_jobs.py --list
   ```

2. **Fast path — requeue (resume from the failed stage).** Best when
   `TRUNCATE_OVERSIZED_CHUNKS=true`. The orchestrator reconciles completed stages from
   the `assets` table, so the job resumes at embed using the **existing** chunks:

   ```powershell
   python services/ekie/scripts/requeue_jobs.py --all-dead --yes   # or --document-id <id>
   python services/ekie/scripts/start_ingest_worker.py             # process the requeued jobs
   ```

   > Because requeue reuses the already-stored chunks, a new smaller
   > `TARGET_TOKEN_BUDGET` is **not** applied by this path. If you set
   > `TRUNCATE_OVERSIZED_CHUNKS=false`, a plain requeue would resume with the same
   > oversized chunks and dead-letter again — use the clean path below instead.

3. **Clean path — re-chunk from source.** Use when you set `truncate=false` or changed
   chunking budgets/strategy and want the new chunking applied. Hard-delete the affected
   documents (removes any partial assets, lineage, jobs, and staged source), then let the
   sync worker re-discover and re-ingest them from the source Markdown:

   ```powershell
   python services/ekie/scripts/purge_documents.py --document-id <id> --yes
   # re-run your normal ingestion (sync worker or POST /v1/documents/{id}/ingest)
   ```

No manual vector cleanup is needed for dead-lettered documents: they never published to
Qdrant, so there is nothing stale to remove. A full clean re-ingest of the whole corpus
is only required when you **change the embedding model or dimension** (Qdrant collection
dimensions cannot change in place — see the Deployment Guide).

#### Async jobs stay `queued` and never run


**Symptom:** With `EKIE_INGESTION__ASYNC_ENABLED=true`, the monitor shows documents as `queued` indefinitely.

**Solution:** Async ingestion requires a running ingest worker. Start it:
```powershell
python services/ekie/scripts/start_ingest_worker.py   # or: ekie-ingest-worker
```

#### Job dead-lettered with "source bytes unavailable for ingestion"

**Symptom:** An async job fails three times and lands in `dead_letter`; `last_error` reads `source bytes unavailable for ingestion`.

**Cause:** The API and worker are separate processes, so the source must be handed off through the shared Control Plane (`ingestion_sources` table). This error means the source was not staged there — typically the API and worker are running mismatched code, or the API was not restarted after upgrading.

**Solution:** Restart the API and the ingest worker so both run the current code, then re-ingest the document (remove its twin so the sync worker re-discovers it — a re-save alone won't re-trigger because change detection is content-hash based).

#### Restarting the ingest worker doesn't pick the job back up

**Symptom:** After killing and restarting the worker, the in-flight document stops progressing and the job stays `running` with no activity.

**Cause:** A hard kill (closing the window) leaves the job locked. A live worker keeps its lock fresh by heartbeating every `EKIE_INGESTION__HEARTBEAT_INTERVAL_SECONDS` (default 15s); a crashed worker stops heartbeating, so its job is reclaimed and resumed once the lock is older than `EKIE_INGESTION__VISIBILITY_TIMEOUT_SECONDS` (default 90s). Stopping with **Ctrl+C** avoids the wait entirely by releasing the job immediately.

**Solution:** Wait up to the visibility timeout (~90s) for automatic reclaim, or requeue the job now (`requeue_jobs.py`). Prefer Ctrl+C over closing the window when stopping the worker. Resume is stage-granular: a job interrupted mid-embedding re-runs that stage from the start (completed earlier stages are reused).

#### Job dead-lettered with "markdown payload unavailable" (or `missing_chunks`)

**Symptom:** After a worker restart, a document dead-letters with `intelligence:missing_markdown: markdown payload unavailable` even though the monitor showed earlier stages complete.

**Cause:** Asset **metadata** is stored in the Control Plane, but asset **payloads** are stored in the asset backend. Older builds used an in-memory backend in local mode, so a restart wiped every payload; on resume, an already-recorded stage was skipped while its bytes were gone, failing the next stage.

**Solution:** Ensure persistent storage is configured (`EKIE_ENVIRONMENT=local` now uses on-disk `LocalFileAssetStorage` at `EKIE_STORAGE__LOCAL_PATH`; see [Deployment Guide 4.3](EKIE-Deployment-Guide.md#43-storage-configuration-assets)). Restart the API and worker, then recover the affected documents:
```powershell
python services/ekie/scripts/recover_lost_payload_docs.py
```

#### Documents stay `waiting` for a long time

**Symptom:** The monitor shows several documents as `waiting · resume …` while only one shows `>>` (running).

**Cause:** This is expected with a single worker (`EKIE_INGESTION__WORKER_CONCURRENCY=1`): documents are processed one at a time and the others queue behind the current job. The `[next]` / `[#N in line]` marker shows each document's position in the claim order.

**Solution:** Let the worker drain the queue (positions count down), or raise a specific job's `priority` to move it ahead. Do **not** run parallel workers for GPU embedding on a single GPU — concurrent embedding jobs contend for VRAM and can OOM.

#### Removing a stuck or unwanted document

**Symptom:** A document is dead-lettered or otherwise unwanted and you want it gone.

**Solution:** Hard-delete it (purges vectors, assets, lineage, jobs, and staged source):
```powershell
python services/ekie/scripts/purge_documents.py --document-id <id> --yes
# or by name / list first:
python services/ekie/scripts/purge_documents.py --source-path "Report.pdf.md" --yes
python services/ekie/scripts/purge_documents.py --list
```

#### `llm_analysis_skipped` in the logs

**Symptom:** The worker logs `llm_analysis_skipped` and the document's topic is heuristic rather than LLM-refined.

**Cause:** The configured `EKIE_INTELLIGENCE__LLM_MODEL` could not be loaded as a text-generation chat model — most commonly because a **vision-language** model (e.g. `Qwen/Qwen2.5-VL-3B-Instruct`) was configured. This is non-fatal: ingestion completes using the deterministic topic.

**Solution:** Set a text instruct model such as `Qwen/Qwen2.5-3B-Instruct`, switch to an Ollama backend, or set `EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS=false`. The real reason is recorded in the warning's structured `reason` field.

#### Unsupported provider value in environment

**Symptom:** EKIE fails startup with settings validation error for provider fields.

**Solution:** Use only supported values:
1. Intelligence provider: `ollama` or `huggingface`.
2. Embedding provider: `local`, `ollama`, or `huggingface`.
3. Publishing provider: `local` or `qdrant`.

Do not edit Python code defaults to change provider. Set these values in `services/ekie/.env`.

#### Langfuse container fails startup with ClickHouse error

**Symptom:**
```
Error: CLICKHOUSE_URL is not configured
```

**Cause:** Recent Langfuse images require ClickHouse configuration for full operation.

**Solution options:**
1. Extend local observability stack with ClickHouse and set `CLICKHOUSE_URL` for Langfuse.
2. Pin to a Langfuse version compatible with your current compose stack.
3. Keep `EKIE_OBSERVABILITY__LANGFUSE_ENABLED=false` until observability stack is fully configured.

**Operator guidance:** Do not mark trace observability complete until Langfuse startup is healthy and traces are visible in UI.

#### Qdrant connection refused

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solution:** Ensure Qdrant is running:
```bash
docker compose -f docker-compose.local.yml up -d qdrant
curl http://localhost:6333/healthz
```

#### Publishing verification failure

```
VerificationError: Missing vectors after publish
```

**Solution:** This indicates vectors were not persisted. Check:
1. Qdrant container logs for errors.
2. Available disk space on the Qdrant volume.
3. Network connectivity between EKIE and Qdrant.

#### MinIO bucket not found

```
StorageError: Bucket 'ekie-assets' not found
```

**Solution:** Create the bucket via MinIO Console (`http://localhost:9006`) or CLI:
```bash
mc alias set local http://localhost:9005 minioadmin minioadmin
mc mb local/ekie-assets
```

### 19.2 Diagnostic Commands

```bash
# Check infrastructure services
docker compose -f docker-compose.local.yml ps

# View EKIE service logs (if running in Docker)
docker logs ekie-service --tail 100

# Test database connectivity
python -c "
from config.settings import get_settings
s = get_settings()
print(s.control_plane.sqlalchemy_url())
"

# List registered parsers
python -c "
from domain.transformation import default_registry
for ext, parser in default_registry().items():
    print(f'{ext}: {type(parser).__name__}')
"

# Validate pipeline for a document
python -c "
from composition import build_pipeline_validator
from domain.control_plane import ControlPlaneDatabase
from domain.storage import InMemoryAssetStorage
# ... setup and validate
"
```

---

## 20. Glossary

| Term | Definition |
|---|---|
| **Asset** | An immutable, versioned artifact derived from a document (markdown, chunks, embeddings, vectors) |
| **Breadcrumb context** | The heading hierarchy path prepended to each chunk for retrieval context |
| **Canonical representation** | Markdown — the universal intermediate format inside EKIE |
| **Control Plane** | The MS SQL Server database that manages all ingestion metadata, state, and lineage |
| **Dead letter** | A workflow that exhausted its retry budget and cannot proceed |
| **Digital Twin** | EKIE's internal representation of a source repository or document's state |
| **Distance metric** | The mathematical function (cosine, dot product, euclidean) used to compare embedding vectors |
| **EKIE** | Enterprise Knowledge Ingestion Engine |
| **EKRE** | Enterprise Knowledge Retrieval Engine (downstream consumer) |
| **EKCP** | Enterprise Knowledge Chat Platform (downstream consumer) |
| **Front matter** | YAML metadata block at the top of a canonical Markdown document |
| **Handoff package** | The validated artifact bundle EKIE produces for EKRE consumption |
| **Lineage** | The directed graph of parent-child relationships between assets |
| **Plugin** | An extension that implements the `EKIEPlugin` protocol and is registered via manifest |
| **Provider** | A swappable backend implementation (e.g., local vs. Ollama for embeddings, local vs. Qdrant for publishing) |
| **Sandbox** | A controlled execution environment for plugin validation |
| **Stage** | One of the five sequential pipeline steps: transformation, intelligence, chunking, embedding, publishing |
| **Tenant** | An organizational unit for multi-tenant data isolation |
| **Workflow** | The orchestrated execution of all pipeline stages for a single document |

---

## 21. PM Owner Runbook

This runbook is the product-owner acceptance flow from environment setup to ingestion proof and observability checks.

### 21.1 Outcome Criteria

A run is accepted when all conditions below are true:
1. EKIE service starts and health probes pass.
2. A markdown file is ingested through EKIE APIs.
3. SQL Control Plane contains document and asset lineage records.
4. Qdrant contains vectors with expected metadata.
5. Workflow status is `completed` for all five stages.
6. Observability path is defined: Langfuse trace visible, or explicit blocker documented with mitigation.

### 21.2 Operator Sequence (No Code Changes)

**Quickest day-to-day launcher — the control panel.** From the repository root,
`.\ekie.ps1` opens a menu to start the API, sync worker, ingest worker, and
monitor (each in its own window), toggle async mode, check health, and
list/purge documents. See the Deployment Guide §6.0.

**Recommended for a full gated deployment: use the deployment task runner:**

```powershell
# Runs all 10 gates with per-gate pass/fail status:
python services/ekie/scripts/deploy.py

# Or after pip install -e services/ekie[...]:
ekie-deploy
```

The runner covers: prerequisites → .env validation → Docker infra → MinIO buckets → SQL schema → Langfuse → HuggingFace model cache → API health → smoke ingest → monitoring verification.

For a manual step-by-step sequence without the runner:

1. Audit repository state
```bash
git status --short
```

2. Select configuration profile
```powershell
Copy-Item services/ekie/.env.profile.hybrid services/ekie/.env -Force
```

3. Start or verify infrastructure
```bash
docker compose -f docker-compose.local.yml up -d
curl http://localhost:6333/collections
```

4. Start EKIE API from service directory so the correct `.env` is loaded
```powershell
# Recommended: use cwd-safe launcher from any directory
python services/ekie/scripts/start_api.py
# Or: ekie-api (if installed via pip install -e)
```

5. Verify EKIE health
```bash
curl http://localhost:8001/health/live
curl http://localhost:8001/health/ready
```

6. Start the sync worker (watches the target folder and submits documents)
```powershell
python services/ekie/scripts/start_worker.py
# Or: ekie-worker
```

7. (Async mode only) Start the ingest worker pool
```powershell
# Required when EKIE_INGESTION__ASYNC_ENABLED=true, otherwise skip.
python services/ekie/scripts/start_ingest_worker.py
# Or: ekie-ingest-worker
```

### 21.3 Markdown Ingestion Validation Flow

1. Create a markdown file in the synced source folder.
2. Call repository ingestion endpoint:
```bash
POST /v1/repositories/{repository_id}/ingest
```
3. Confirm response fields:
- `attempted > 0`
- `completed > 0`
- `dead_lettered = 0` for happy path
- completed stages include: `transform`, `intelligence`, `chunk`, `embed`, `publish`

Example local validation values:
1. Repository: `0ba1139f-c30c-439c-a2e9-2c1f1a776342`
2. Tenant: `ekie-tenant`
3. Ingested document: `000_pm_owner_validation.md`

PowerShell example:
```powershell
$mdPath = 'D:\Octave\AI training\test\000_pm_owner_validation.md'
@'
# EKIE PM Validation

This markdown file validates end-to-end ingestion.
'@ | Set-Content -Path $mdPath -Encoding UTF8

$headers = @{ 'X-Tenant-ID' = 'ekie-tenant'; 'Content-Type' = 'application/json' }
$body = '{"sync_before_ingest":true,"max_documents":1}'
Invoke-RestMethod -Method Post -Uri 'http://localhost:8001/v1/repositories/0ba1139f-c30c-439c-a2e9-2c1f1a776342/ingest' -Headers $headers -Body $body | ConvertTo-Json -Depth 10
```

### 21.4 SQL Verification Checklist

Run SQL checks in the Control Plane database after ingestion.

1. Document row exists and is active in `documents`.
2. Asset lineage exists in `assets` for expected types:
- `markdown`
- `intelligence`
- `chunks`
- `embedding`
- `vector`
3. Workflow status API endpoint reports `completed`.

SQL examples (Windows Authentication):
```powershell
sqlcmd -S "localhost\MSSQLSERVER2022" -E -C -d ekrag_control_plane -Q "SELECT TOP 5 id, source_path, status, updated_at FROM documents WHERE tenant_id='ekie-tenant' AND source_path LIKE '%000_pm_owner_validation.md' ORDER BY updated_at DESC;"

sqlcmd -S "localhost\MSSQLSERVER2022" -E -C -d ekrag_control_plane -Q "SELECT TOP 20 document_id, asset_type, version, created_at FROM assets WHERE document_id IN (SELECT id FROM documents WHERE source_path LIKE '%000_pm_owner_validation.md') ORDER BY created_at DESC;"
```

### 21.5 Qdrant Verification Checklist

1. Collection exists (`enterprise_documents` or model-scoped variant).
2. Point count is greater than zero.
3. Payload metadata includes:
- `metadata.document_id`
- `metadata.tenant_id`
- `metadata.embedding_model`
- `metadata.dimension`
- `metadata.repository_id`

Qdrant examples:
```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:6333/collections' | ConvertTo-Json -Depth 10

$payload = @{ limit = 1; with_payload = $true; with_vector = $false } | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method Post -Uri 'http://localhost:6333/collections/enterprise_documents/points/scroll' -ContentType 'application/json' -Body $payload | ConvertTo-Json -Depth 10
```

Deletion verification for source-removed files:
1. Delete a file from the synced repository path.
2. Trigger repository sync + ingest.
3. Confirm the cleanup endpoint path executes successfully.

PowerShell example:
```powershell
$headers = @{ 'X-Tenant-ID' = 'ekie-tenant'; 'Content-Type' = 'application/json' }
Invoke-RestMethod -Method Post -Uri 'http://localhost:8001/v1/repositories/0ba1139f-c30c-439c-a2e9-2c1f1a776342/ingest' -Headers $headers -Body '{"sync_before_ingest":true}' | ConvertTo-Json -Depth 10
```

Expected behavior:
1. Deleted document no longer appears as active in `documents`.
2. Vector cleanup is triggered for `DocumentDeleted` sync events.
3. Qdrant points for the deleted document are removed.

### 21.6 Worker Monitoring Model

Use the built-in live progress monitor to watch ingestion as the worker runs. It reads directly from the Control Plane database and refreshes every few seconds:

```powershell
# Terminal C (alongside API and worker):
python services/ekie/scripts/monitor.py

# Or after pip install -e services/ekie[...]:
ekie-monitor
```

Options:

```powershell
# Custom tenant and refresh rate:
python services/ekie/scripts/monitor.py --tenant-id tenant-default --refresh 3

# Show all documents (default: top 40 by activity):
python services/ekie/scripts/monitor.py --all
```

What the monitor shows:

```
╭──────────────────────── EKIE Ingestion Monitor ────────────────────────╮
│  Tenant: tenant-default   Refresh: 2s   Time: 19:13:40                   │
│                                                                          │
│  xxxxxxxxxx..........  50%  1 complete  1 running  0 queued  of 2 total  │
╰──────────────────────────────────────────────────────────────────────────╯

 Document          T I C E P   Status            Stage Metrics        Last
 PlantState…       x x x . .   >> E 128/260 49%  T  168467ch          36s
                                                 I  291§ 25201t ...
                                                 C  260ch 24451t
 New Text Doc.txt  x x x x x   complete          T  269ch ...         68h

╭─ Legend ────────────────────────────────────────────────────────────────╮
│  Stages   x=done  .=pending   T Transform  I Intelligence  C Chunking ... │
│  Status   complete   >> E 128/260 49% (running: stage + done/total)   ... │
│  Metrics  T ch=chars   I §=sections t=tokens ...   C ch=chunks t=tokens   │
│           E em=embeddings t=tokens b=batches d=dim   P v=vectors ✓=verif. │
│  Last     time since newest stage asset                    Ctrl+C to exit │
╰──────────────────────────────────────────────────────────────────────────╯
```

**Columns:**

| Column | Meaning |
|--------|---------|
| **Document** | Source file name. |
| **T I C E P** | Per-stage pipeline bar: `x` = complete, `.` = pending. |
| **Status** | `complete`; `>> <stage> <done>/<total> <pct>%` (running, with live intra-stage progress); `queued`; or `dead-letter`. |
| **Stage Metrics** | Per-stage counters for completed stages, **one stage per line** (decoded in the Legend). |
| **Last** | Time since the most recent stage asset was written for that document. |

The **Status** column shows real, live within-stage progress: while a document is
embedding, it advances `>> E 1/260 → 260/260 100%` as each batch of chunks is
processed (published to the Control Plane per batch). The **Legend** panel at the
bottom is a static key, organized by category (Stages / Status / Metrics / Last).

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

A condensed version of this legend is always rendered at the bottom of the monitor window for quick reference.

The monitor reads the Control Plane directly (no API call required) so it stays accurate even while a long ingestion is in progress. Press **Ctrl+C** to exit.

### 21.6.1 Asynchronous Ingestion Worker

Large documents can exceed the API's HTTP read timeout when the pipeline runs
inline. Enable the durable job queue so ingestion runs out of the request path
with retries and dead-lettering:

```powershell
# 1. In services/ekie/.env:
#    EKIE_INGESTION__ASYNC_ENABLED=true

# 2. Run one or more ingest workers alongside the API and sync worker:
python services/ekie/scripts/start_ingest_worker.py
# Or: ekie-ingest-worker
```

Behavior when enabled:
- `POST /v1/documents/{id}/ingest` stages the source bytes in the Control Plane (`ingestion_sources`), enqueues a job, and returns `202 Accepted` with a `job_id`. Because the worker is a separate process, the source is handed off through the shared database, not process-local memory.
- The ingest worker claims jobs, runs the pipeline (or a deletion), and marks the job `succeeded` (deleting the staged source), or requeues with exponential backoff up to `EKIE_INGESTION__MAX_ATTEMPTS` before `dead_letter`.
- **Graceful restart:** stopping the worker with **Ctrl+C** returns its in-flight job to the queue immediately (no retry spent), so a restarted worker resumes it at once.
- **Hard-kill recovery:** a live worker heartbeats its lock every `EKIE_INGESTION__HEARTBEAT_INTERVAL_SECONDS` (15s); if the worker is killed abruptly, its job is reclaimed and resumed once the lock is older than `EKIE_INGESTION__VISIBILITY_TIMEOUT_SECONDS` (default 90s).
- **Persistent payloads:** stage outputs are written to disk (`EKIE_STORAGE__LOCAL_PATH`), so a resumed job re-reads completed-stage payloads instead of failing.
- Poll `GET /v1/documents/{id}/job` for status. The monitor also shows `queued`, `waiting` (queued to resume, with queue position), live `running` progress, and red `dead-letter` rows.

Tuning keys live under `EKIE_INGESTION__*` (see `.env.example`). With async
disabled (default), ingestion runs inline and no ingest worker is needed.

### 21.6.2 Deleting Documents and Cleaning Up Orphans

Deletion is a hard delete: it purges the document's vectors from the vector
store and removes its Control Plane rows (assets, workflows, and processing
state cascade). The sync worker performs this automatically when a source file
is removed.

Delete a single document via the API:
```bash
curl -X DELETE "http://localhost:8001/v1/documents/{document_id}?force=false" \
  -H "X-Tenant-ID: tenant-default"
```

Bulk or orphaned cleanup uses the maintenance tool. Orphaned documents occur
when `EKIE_SYNC__TARGET_DIRECTORY` is repointed at a new folder: documents from
the previous folder are no longer scanned and cannot be delete-detected.

```powershell
# Inspect current documents grouped by repository:
python services/ekie/scripts/purge_documents.py --list

# Remove documents whose repository no longer matches the current target:
python services/ekie/scripts/purge_documents.py --orphaned --force --yes

# Remove a specific document, or every soft-deleted row:
python services/ekie/scripts/purge_documents.py --source-path "old.md" --force --yes
python services/ekie/scripts/purge_documents.py --status deleted --force --yes

# Drop repository records that have no remaining documents:
python services/ekie/scripts/purge_documents.py --drop-empty-repositories --yes
```

The tool prints the affected documents and prompts for confirmation unless
`--yes` is passed. It also purges the corresponding vectors from Qdrant.

### 21.7 Langfuse Monitoring Path

Langfuse observability is active in the current configuration.

Required `.env` settings (already enabled):
```dotenv
EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true
EKIE_ORCHESTRATION__RUNNER=langgraph
EKIE_ORCHESTRATION__ENABLE_TRACING=true
```

Start the Langfuse stack if not already running:
```powershell
docker compose -f docker-compose.local.yml up -d clickhouse langfuse-db langfuse
docker compose -f docker-compose.local.yml ps clickhouse langfuse-db langfuse
```

All services should show `(healthy)` before starting EKIE. Open http://localhost:3000 to access the Langfuse UI.

Verification:
1. Trigger an ingestion request with `X-Correlation-ID` header.
2. Confirm the same correlation ID appears in EKIE structured logs.
3. Confirm a trace appears in Langfuse for that run.

If the Langfuse container fails to become healthy, check:
```powershell
docker logs enterprise-knowledge-rag-system-clickhouse-1 --tail 20
docker logs enterprise-knowledge-rag-system-langfuse-1 --tail 20
```

**Langfuse worker Redis auth errors.** If the `langfuse-worker` container floods
logs with `ERR AUTH <password> called without any password configured` (its
`monitor-queue` timing out), the Redis client and server disagree on
authentication. The compose file now runs Redis with a password
(`--requirepass ${REDIS_PASSWORD:-langfuse_redis}`) and passes the same value to
Langfuse via `REDIS_AUTH`, so both sides match. Recreate the affected containers
to apply it:
```powershell
docker compose -f docker-compose.local.yml up -d redis langfuse langfuse-worker
```
This Redis instance serves Langfuse only — EKIE's own job queue is Control-Plane
(database) backed and does not use Redis.

### 21.8 Production Handover Notes

1. Keep profile-based configuration for fast rollback.
2. Use `model_scoped` publishing strategy when switching embeddings frequently.
3. Never change provider defaults in code for routine operations.
4. Record each deployment with profile name, repository ID, correlation ID, SQL verification output, and Qdrant verification output.

### 21.9 Acceptance Evidence Template

Use this template for each execution cycle:

```text
Run Date:
Operator:
Profile Applied:
Repository ID:
Tenant ID:
Correlation ID:

EKIE Health:
- /health/live:
- /health/ready:

Ingestion Result:
- attempted:
- completed:
- dead_lettered:
- completed_stages:

SQL Evidence:
- documents row present: yes/no
- assets include markdown/intelligence/chunks/embedding/vector: yes/no

Qdrant Evidence:
- collection name:
- point count:
- payload contains metadata.document_id/tenant_id/model/dimension/repository_id: yes/no

Langfuse Evidence:
- service healthy: yes/no
- trace visible for correlation ID: yes/no
- blocker (if any):

Decision:
- accepted / rejected
- follow-up actions:
```

### 21.10 One-Command Acceptance Report

Use the built-in script to run health checks, ingest a markdown file, validate SQL and Qdrant evidence, and produce a machine-readable report:

```powershell
python services/ekie/scripts/acceptance_report.py
```

Optional flags:
1. `--tenant-id <tenant>`
2. `--repository-id <repository_id>`
3. `--source-dir <directory>`
4. `--ekie-url <base_url>`
5. `--langfuse-url <base_url>`
6. `--report-dir <directory>`
7. `--max-documents <n>`
8. `--skip-ingest` (health-only mode)

Default report output directory:
1. `services/ekie/storage`
2. Filename format: `acceptance_report_YYYYMMDD_HHMMSS.json`

### 21.11 Document Conversion (EKDC) Operations Checklist

EKIE ingests Markdown only. Converting source files (PDF, DOCX, PPTX, HTML, CSV,
images, audio, video) to Markdown is owned by the EKDC agent (`services/ekdc`),
which runs as a separate process and writes `.md` files, preserving the input
folder structure. Use this checklist to prepare the Markdown that EKIE ingests.

Setup steps:
1. Install EKDC dependencies (in the EKDC environment, not EKIE):
```powershell
pip install -r services/ekdc/requirements.txt
```
2. Configure the EKDC input/output directories (via `services/ekdc/.env`):
```dotenv
INPUT_DIRECTORY=D:\Enterprise\SourceDocuments
OUTPUT_DIRECTORY=D:\Enterprise\Markdown
```
3. Run the EKDC agent to convert existing files and watch for changes:
```powershell
python services/ekdc/agent.py
```

Handoff to EKIE:
1. Point EKIE at the EKDC output folder so it ingests the generated Markdown:
```dotenv
EKIE_SYNC__TARGET_DIRECTORY=D:\Enterprise\Markdown
EKIE_SYNC__ALLOWED_EXTENSIONS=md
```
2. Start the EKIE worker; it syncs and ingests the `.md` files (see Section 8).

Troubleshooting:
1. If a document is missing from EKIE, confirm EKDC produced the corresponding
   `.md` file in `OUTPUT_DIRECTORY` (EKDC logs to `ekdc_agent.log`).
2. EKIE no longer bundles OCR or rich-media libraries; extraction quality issues
   are addressed in EKDC's converter, not in EKIE.

---

> **For the detailed architecture handbook** (22 chapters covering enterprise architecture principles, repository synchronization, chunking algorithms, embedding mathematics, disaster recovery, and operations runbooks), see [EKIE-handbook.md](EKIE-handbook.md).

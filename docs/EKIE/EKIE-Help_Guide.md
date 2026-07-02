# EKIE — Enterprise Knowledge Ingestion Engine

## Complete Documentation & Operations Guide

> **Version:** 1.0
> **Status:** Approved
> **Audience:** Engineers, DevOps, Platform Operators
> **Last Updated:** 2026-07-02

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

---

## 1. Introduction

### 1.1 What is EKIE?

EKIE (Enterprise Knowledge Ingestion Engine) is a dedicated enterprise platform that transforms heterogeneous enterprise documents into governed, versioned, traceable, and AI-ready knowledge assets. It is the ingestion layer of the three-engine EK-RAG architecture.

### 1.2 What EKIE Does

| Capability | Description |
|---|---|
| Repository synchronization | Continuously syncs enterprise repositories (file systems, SharePoint, Git) |
| Document transformation | Converts any supported format into canonical Markdown |
| Document intelligence | Extracts metadata, detects language, classifies content, identifies sensitive data |
| Intelligent chunking | Splits Markdown into semantically meaningful chunks preserving structure |
| Embedding generation | Generates vector embeddings via local or Ollama providers |
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
Enterprise Repositories
       │
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
Source Document
  → Repository Sync (Digital Twin created/updated)
    → Transformation (raw bytes → canonical Markdown)
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
| **Ollama** | Latest | Local LLM and embedding models |
| **Node.js** | 18+ | Web UI (separate `apps/web-ui/` project) |

### 3.3 Hardware Recommendations

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 20 GB free | 50+ GB SSD |
| GPU | Not required | NVIDIA GPU for Ollama acceleration |

---

## 4. Project Structure

```
Enterprise-Knowledge-RAG-System/
├── docs/
│   └── EKIE/
│       ├── EKIE-handbook.md          # Architecture handbook (22 chapters)
│       └── EKIE-documentation.md     # This document
├── packages/
│   └── contracts/                    # Shared cross-engine Pydantic v2 schemas
│       └── src/
├── services/
│   └── ekie/
│       ├── .env.example              # Configuration template (180 variables)
│       ├── pyproject.toml            # Project metadata and dependencies
│       ├── scripts/                  # Demo scripts for each subsystem
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

# EKIE service with development extras
pip install -e "services/ekie[dev,mssql]"

# Shared contracts package
pip install -e packages/contracts
```

### 5.4 Configure Environment Variables

```bash
# Copy the EKIE configuration template
cp services/ekie/.env.example services/ekie/.env
```

Edit `services/ekie/.env` and set your local values. The critical values to configure:

```dotenv
# Control Plane database password
EKIE_CONTROL_PLANE__PASSWORD=YourStrongPassword123!

# MinIO object storage credentials
EKIE_STORAGE__ACCESS_KEY=minioadmin
EKIE_STORAGE__SECRET_KEY=minioadmin
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

---

## 6. Configuration Reference

> **Note:** This entire section is for **informational reference only**. For your initial setup, you only need to configure the critical variables mentioned in [Section 5.4](#54-configure-environment-variables). You do not need to perform any actions in this section unless you want to customize EKIE's default behavior.

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
| `EKIE_QDRANT__REQUEST_TIMEOUT_SECONDS` | `30.0` | Request timeout |

#### Redis (Cache)

| Variable | Default | Description |
|---|---|---|
| `EKIE_REDIS__HOST` | `localhost` | Redis hostname |
| `EKIE_REDIS__PORT` | `6379` | Redis port |

#### MinIO (Object Storage)

| Variable | Default | Description |
|---|---|---|
| `EKIE_STORAGE__ENDPOINT` | `localhost:9000` | MinIO endpoint |
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
| `EKIE_TRANSFORMATION__IMAGE_HANDLING` | `reference` | `reference`, `ignore_decorative`, or `ocr` |
| `EKIE_TRANSFORMATION__OCR_ENABLED` | `false` | Enable OCR processing |

#### Document Intelligence

| Variable | Default | Description |
|---|---|---|
| `EKIE_INTELLIGENCE__DETECT_LANGUAGE` | `true` | Auto-detect language |
| `EKIE_INTELLIGENCE__CLASSIFY_CONTENT` | `true` | Classify document type |
| `EKIE_INTELLIGENCE__DETECT_SENSITIVE_CONTENT` | `true` | Detect PII/sensitive data |
| `EKIE_INTELLIGENCE__HIGH_COMPLEXITY_SECTION_THRESHOLD` | `12` | Section complexity threshold |
| `EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS` | `false` | Enable LLM-based topic analysis |
| `EKIE_INTELLIGENCE__LLM_PROVIDER` | `ollama` | `ollama` or `huggingface` |
| `EKIE_INTELLIGENCE__LLM_MODEL` | `llama3.1` | LLM model name |
| `EKIE_INTELLIGENCE__LLM_BASE_URL` | `http://localhost:11434` | LLM endpoint |
| `EKIE_INTELLIGENCE__LLM_TEMPERATURE` | `0.0` | LLM temperature (deterministic) |

> **Note on using HuggingFace locally for Intelligence:** To use a HuggingFace LLM (e.g., `Qwen/Qwen2.5-7B-Instruct`) for topic analysis, install the dependencies (`pip install langchain-huggingface torch transformers accelerate`). Then set `EKIE_INTELLIGENCE__ENABLE_LLM_ANALYSIS=true`, `EKIE_INTELLIGENCE__LLM_PROVIDER=huggingface`, and update `EKIE_INTELLIGENCE__LLM_MODEL` to your model ID. The model weights will be downloaded and cached in your `HF_HOME` directory.

#### Intelligent Chunking

| Variable | Default | Description |
|---|---|---|
| `EKIE_CHUNKING__DEFAULT_STRATEGY` | `semantic` | Strategy: `semantic`, `section_based`, `heading_based`, `paragraph_based`, `token_based`, `table_based`, `code_based` |
| `EKIE_CHUNKING__TARGET_TOKEN_BUDGET` | `512` | Target chunk size in tokens |
| `EKIE_CHUNKING__MAX_TOKEN_BUDGET` | `1024` | Maximum chunk size in tokens |
| `EKIE_CHUNKING__MIN_CHUNK_TOKENS` | `8` | Minimum chunk size (drop below this) |
| `EKIE_CHUNKING__PRESERVE_TABLES` | `true` | Keep tables as atomic chunks |
| `EKIE_CHUNKING__PRESERVE_CODE` | `true` | Keep code blocks as atomic chunks |
| `EKIE_CHUNKING__RESPECT_SECTION_BOUNDARIES` | `true` | Do not split across section headings |
| `EKIE_CHUNKING__INCLUDE_BREADCRUMB_CONTEXT` | `true` | Prepend heading hierarchy to chunks |

#### Embedding Framework

| Variable | Default | Description |
|---|---|---|
| `EKIE_EMBEDDING__PROVIDER` | `local` | `local` (hash), `ollama`, or `huggingface` |
| `EKIE_EMBEDDING__DEFAULT_MODEL` | `local-hash-256` | Model identifier |
| `EKIE_EMBEDDING__DIMENSION` | `256` | Embedding dimensionality |
| `EKIE_EMBEDDING__DISTANCE_METRIC` | `cosine` | `cosine`, `dot_product`, or `euclidean` |
| `EKIE_EMBEDDING__MAX_INPUT_TOKENS` | `8192` | Maximum input token limit |
| `EKIE_EMBEDDING__BATCH_SIZE` | `16` | Batch size for embedding requests |
| `EKIE_EMBEDDING__NORMALIZE_VECTORS` | `true` | L2-normalize output vectors |
| `EKIE_EMBEDDING__MAX_RETRIES` | `3` | Retry count on provider failures |
| `EKIE_EMBEDDING__OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |

> **Note on using HuggingFace locally:** To use HuggingFace embedding models locally without Ollama (e.g., `Qwen/Qwen3-VL-Embedding-8B`), you must first install the dependency (`pip install langchain-huggingface sentence-transformers`). Then set `EKIE_EMBEDDING__PROVIDER=huggingface`, update `EKIE_EMBEDDING__DEFAULT_MODEL` to your model ID, and ensure `EKIE_EMBEDDING__DIMENSION` matches the model's output size. To prevent re-downloading the model weights every time, set the `HF_HOME` environment variable to a persistent local directory (e.g., `HF_HOME=./.hf_cache`).

#### Vector Publishing

| Variable | Default | Description |
|---|---|---|
| `EKIE_PUBLISHING__PROVIDER` | `local` | `local` (in-memory) or `qdrant` |
| `EKIE_PUBLISHING__DEFAULT_COLLECTION` | `enterprise_documents` | Target collection name |
| `EKIE_PUBLISHING__BATCH_SIZE` | `64` | Batch size for upserts |
| `EKIE_PUBLISHING__MAX_RETRIES` | `3` | Retry count on publish failures |
| `EKIE_PUBLISHING__CREATE_MISSING_COLLECTIONS` | `true` | Auto-create collections |
| `EKIE_PUBLISHING__VERIFY_AFTER_PUBLISH` | `true` | Verify vectors after publish |

### 6.4 Orchestration Settings

| Variable | Default | Description |
|---|---|---|
| `EKIE_ORCHESTRATION__RUNNER` | `sequential` | `sequential` or `langgraph` |
| `EKIE_ORCHESTRATION__MAX_ATTEMPTS_PER_STAGE` | `3` | Max retries per pipeline stage |
| `EKIE_ORCHESTRATION__RETRY_BACKOFF_BASE_SECONDS` | `0.0` | Backoff base (0 = no sleep) |
| `EKIE_ORCHESTRATION__RETRY_BACKOFF_MULTIPLIER` | `2.0` | Exponential backoff multiplier |
| `EKIE_ORCHESTRATION__ENABLE_TRACING` | `false` | Emit Langfuse traces |

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

The project provides a Docker Compose file that starts all required services:

```bash
docker compose -f docker-compose.local.yml up -d
```

This starts the following services:

| Service | Port | Purpose |
|---|---|---|
| **MS SQL Server 2022** | `1433` | Control Plane database |
| **Qdrant** | `6333` | Vector database |
| **Redis 7** | `6379` | Cache layer |
| **MinIO** | `9000` (API), `9001` (Console) | Object storage |
| **Langfuse** | `3000` | Observability (LLM tracing) |
| **PostgreSQL 16** | *(internal)* | Langfuse internal store only |

> **Important:** The PostgreSQL instance exists solely as Langfuse's internal store. It is NOT an application database. The EK-RAG control plane uses Microsoft SQL Server.

### 7.2 Verify Services

```bash
# Check all containers are running
docker compose -f docker-compose.local.yml ps

# Verify Qdrant
curl http://localhost:6333/healthz

# Verify MinIO
curl http://localhost:9000/minio/health/live

# Verify MS SQL Server connectivity
# (requires sqlcmd or equivalent client)
sqlcmd -S localhost,1433 -U sa -P "YourPassword" -Q "SELECT 1"
```

### 7.3 Create the Control Plane Database

Connect to MS SQL Server and create the database:

```sql
CREATE DATABASE ekrag_control_plane;
GO
```

> **Note:** When `EKIE_ENVIRONMENT=local`, the application auto-provisions the schema on startup via `db.create_all()`. No manual table creation is needed.

### 7.4 Create MinIO Bucket

Access the MinIO Console at `http://localhost:9001` and create a bucket named `ekie-assets`, or use the MinIO client:

```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/ekie-assets
```

### 7.5 Optional: Install Ollama for Real Embeddings

For production-quality embeddings (beyond the deterministic hash provider):

```bash
# Install Ollama (see https://ollama.ai)
# Pull an embedding model
ollama pull nomic-embed-text

# Update .env to use Ollama embeddings
# EKIE_EMBEDDING__PROVIDER=ollama
# EKIE_EMBEDDING__DEFAULT_MODEL=nomic-embed-text
# EKIE_EMBEDDING__DIMENSION=768
```

---

## 8. Running the Service

### 8.1 Start the EKIE API Server

```bash
cd services/ekie

# Start with uvicorn (development)
uvicorn src.api.app:app --host 0.0.0.0 --port 8001 --reload

# Or from the project root
.venv/Scripts/python.exe -m uvicorn api.app:app --host 0.0.0.0 --port 8001 --reload --app-dir services/ekie/src
```

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

Run the full ingestion workflow for a synced document. The raw document bytes are sent in the request body.

**Parameters:**
- `document_id` (path, required): The document ID from the Control Plane
- `mime_type` (query, optional): MIME type hint (e.g., `text/markdown`, `text/plain`)
- `intelligence_provider` (query, optional): Override the LLM provider for document analysis (e.g., `huggingface` or `ollama`).
- `intelligence_model` (query, optional): Override the LLM model used for analysis (e.g., `meta-llama/Llama-3-8b-chat-hf`).
- `embedding_provider` (query, optional): Override the embedding provider (e.g., `huggingface` or `ollama`).
- `embedding_model` (query, optional): Override the embedding model used for vector generation.

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

Converts raw document bytes into canonical Markdown.

**How it works:**
1. A format-specific parser is selected from the `ParserRegistry` based on MIME type or file extension.
2. The parser extracts text content and metadata from the raw bytes.
3. The content is normalized (Unicode normalization, blank line collapsing).
4. A `MarkdownDocument` is produced with YAML front matter containing source metadata.
5. The document passes `MarkdownValidator` checks.
6. The Markdown and its content hash are stored as an immutable asset in the Control Plane.

**Supported Formats:**

| Format | Parser | Extensions |
|---|---|---|
| Markdown | `MarkdownParser` | `.md`, `.markdown` |
| Plain text | `PlainTextParser` | `.txt`, `.text` |
| CSV | `CsvParser` | `.csv` |
| HTML | `HtmlParser` | `.html`, `.htm` |
| Source code | `SourceCodeParser` | `.py`, `.js`, `.ts`, `.java`, etc. |

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
9. **LlmAnalyzer** *(optional)* — Uses a local Ollama model for advanced topic extraction and summarization.

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
| `ollama` | `EKIE_EMBEDDING__PROVIDER=ollama` | Real neural embeddings via a locally-hosted Ollama model. Recommended models: `nomic-embed-text` (768d), `mxbai-embed-large` (1024d). |

**Features:**
- **Model registry**: Validates model compatibility and tracks model specifications.
- **Batch processing**: Chunks are embedded in configurable batches.
- **Cost estimation**: Tracks estimated token costs per embedding operation.
- **Retry with backoff**: Provider failures trigger exponential backoff retries.
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

- `AssetStorage` (protocol): Store and retrieve binary assets by key.
- `InMemoryAssetStorage`: Default in-process store for development and testing.
- `compute_content_hash`: SHA-256 hash for content integrity.

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
    description="Custom PDF parser with OCR",
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

For LLM/agent observability:

```dotenv
EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true
EKIE_OBSERVABILITY__LANGFUSE_HOST=http://localhost:3000
EKIE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY=pk-...
EKIE_OBSERVABILITY__LANGFUSE_SECRET_KEY=sk-...
```

When enabled with the `langgraph` runner, the orchestrator emits traces to the self-hosted Langfuse instance.

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

### 18.1 Environment Profiles

| Environment | Key Settings |
|---|---|
| **Local (default)** | `ENVIRONMENT=local`, local providers, in-memory storage, auto-schema provision |
| **Staging** | `ENVIRONMENT=staging`, Qdrant + Ollama providers, MS SQL, MinIO |
| **Production** | `ENVIRONMENT=production`, full stack, authentication required, >=2 replicas |

### 18.2 Production Configuration Checklist

- [ ] `EKIE_SECURITY__REQUIRE_AUTHENTICATION=true`
- [ ] `EKIE_EMBEDDING__PROVIDER=ollama` (or another real provider)
- [ ] `EKIE_PUBLISHING__PROVIDER=qdrant`
- [ ] `EKIE_CONTROL_PLANE__PASSWORD` set to a strong password
- [ ] `EKIE_STORAGE__ACCESS_KEY` and `SECRET_KEY` set
- [ ] `EKIE_GOVERNANCE__ENABLE_AUDIT=true`
- [ ] `EKIE_GOVERNANCE__AUDIT_SINK=logging`
- [ ] `EKIE_PLUGINS__ALLOW_UNSIGNED=false`
- [ ] `EKIE_PLUGINS__REQUIRE_SIGNATURE=true`
- [ ] `EKIE_DEPLOYMENT__REPLICAS=2` (or higher)
- [ ] `EKIE_OBSERVABILITY__LANGFUSE_ENABLED=true`

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

**Solution:** Ensure `EKIE_EMBEDDING__DIMENSION` matches the actual output dimension of your embedding model. For example, `nomic-embed-text` outputs 768 dimensions.

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

**Solution:** Create the bucket via MinIO Console (`http://localhost:9001`) or CLI:
```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
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

> **For the detailed architecture handbook** (22 chapters covering enterprise architecture principles, repository synchronization, chunking algorithms, embedding mathematics, disaster recovery, and operations runbooks), see [EKIE-handbook.md](EKIE-handbook.md).

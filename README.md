# Enterprise Knowledge RAG System (EK-RAG)

Welcome to the Enterprise Knowledge RAG System (EK-RAG) repository.

EK-RAG is a fully decoupled, production-grade Retrieval-Augmented Generation platform built around three independent, specialized engines. Rather than building a monolithic chatbot-plus-search application, this repository orchestrates ingestion, retrieval, and chat orchestration as highly scalable, distinct microservices.

## 📖 Architecture & Documentation
The system architecture is entirely decoupled and documented. Before contributing, you **must** read the Master Architecture Blueprint to understand how the three engines integrate.

- **[Master Architecture Blueprint](docs/master-architecture.md):** Start here. Covers the end-to-end topology, data flow, and global integration contracts (Vector Mismatches, Citations, DSAR Purging, and HTTP 429 Backpressure).
- **[EKIE - Enterprise Knowledge Ingestion Engine](docs/EKIE/EKIE-handbook.md):** The factory. Connects to repositories, extracts intelligence, chunks, and publishes embeddings.
- **[EKRE - Enterprise Knowledge Retrieval Engine](docs/EKRE/EKRE-handbook.md):** The librarian. Handles query intelligence, vector/keyword math, candidate fusion, and citation lineage.
- **[EKCP - Enterprise Knowledge Chat Platform](docs/EKCP/EKCP-handbook.md):** The brain. Manages conversation digital twins, memory, agent tools, and LLM prompting.

## 🏗️ Repository Structure (Monorepo)
We utilize a domain-isolated monorepo structure. Engines cannot share databases or internal states. They communicate exclusively via REST APIs and Event Buses.

```
/docs                       # Enterprise architecture specifications and handbooks
/docs/sprints               # Per-engine and master integration sprint tracks
/services/ekie              # Ingestion Engine (Python/FastAPI)
/services/ekre              # Retrieval Engine (Python/FastAPI)
/services/ekcp              # Chat Platform (Python/FastAPI)
/services/<engine>/src/config   # Centralized settings (environment-backed)
/services/<engine>/src/api      # FastAPI routers and handlers
/services/<engine>/src/domain   # Engine domain logic
/services/<engine>/tests        # Service tests
/packages/contracts         # Shared cross-engine Pydantic v2 schemas
```

## 🗺️ Delivery Planning
Delivery follows a foundation-first, gate-driven plan. Start with the sprint index, then the per-engine tracks.

- **[Sprint Plan (Index)](docs/sprint-plan.md):** Track model, sequence, and blocking quality gates.
- **[Sprint Tracks](docs/sprints):** Foundation, EKIE, EKRE, EKCP, and Master Integration tracks mapped to handbook chapters.

## 🛠️ Development & Coding Rules
This project enforces strict enterprise coding standards. Always-on guardrails for AI coding agents live in [.github/copilot-instructions.md](.github/copilot-instructions.md) and [.agents/AGENTS.md](.agents/AGENTS.md).

- **Core stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy.
- **Type Safety:** 100% strict type hinting is mandatory (`mypy --strict`).
- **Validation:** All cross-engine payloads must be strongly typed using Pydantic v2 models from `/packages/contracts`.
- **No hardcoding:** Credentials, URLs, ports, and tunables come from environment-backed settings modules; user-adjustable defaults live in `.env.example`.

## 🤖 Reference Implementation Stack
The architecture remains vendor-neutral (Technology Independence). The current reference implementation standardizes on:

- **Orchestration & agents:** LangChain and LangGraph (behind engine-owned abstractions so the core stays model-independent).
- **LLM/embeddings:** provider-abstracted gateway; distance metric is inherited from EKIE, never hardcoded in EKRE.
- **Vector DB:** Qdrant. **Cache:** Redis. **Object storage:** MinIO (self-hosted, local). **Control plane:** Microsoft SQL Server (no PostgreSQL, no cloud).
- **Observability:** Langfuse (self-hosted) for LLM/agent tracing plus OpenTelemetry for traces/metrics, with structured JSON logging carrying `tenant_id` and `correlation_id`.

## 🚀 Getting Started (Local Setup)

Because the entire infrastructure (Qdrant, Redis, MinIO, MS SQL Server, Ollama) runs locally via containers, you must have Docker installed before you can start the system.

### 1. Install Docker Desktop
If you do not have Docker installed, please download and install **Docker Desktop**:
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)

*Note for Windows users: Ensure that you have WSL 2 (Windows Subsystem for Linux) installed and enabled as your backend in Docker Desktop settings.*

### 2. Configure Environment and Start Local Infrastructure
First, you must create a `.env` file at the root of the project to provide credentials for the Docker containers. Copy the provided template:
```bash
# On Windows PowerShell
Copy-Item .env.example .env
# On Mac/Linux
cp .env.example .env
```
Open the `.env` file and set strong passwords (e.g., `MINIO_ROOT_PASSWORD`, `MSSQL_SA_PASSWORD`).

Once Docker is installed and your `.env` is configured, open your terminal in the root of this project and run:
```bash
docker compose -f docker-compose.local.yml up -d
```
This will download and start the local databases, vector stores, and caches in the background. You can verify they are running with:
```bash
docker compose -f docker-compose.local.yml ps
```

### 3. Setup the Python Environment
Create a virtual environment and install the root dependencies to test all services locally:
```bash
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### 4. Common Troubleshooting & Notes
- **Qdrant Setup:** Qdrant is fully managed by Docker and stores its vector data in a managed Docker volume (`qdrant_data`). You do not need to manually install, copy, or paste any Qdrant files into the services directories.
- **MinIO Port Conflicts:** If MinIO fails to start (e.g., `bind: An attempt was made to access a socket in a way forbidden`), port `9000` is likely reserved by a Windows system process. To fix this, change `MINIO_PORT=9005` in your root `.env` and update the `EKIE_STORAGE__ENDPOINT=localhost:9005` in `services/ekie/.env` (and any other services connecting to it).
- **Connecting to Local SQL Server with Windows Authentication:** If you are using your own local SQL Server native instance instead of the Docker container, ensure you specify the named instance. Additionally, Microsoft ODBC Driver 18 strictly enforces encryption. When using `sqlcmd` with Windows Authentication (`-E`) against a local server with self-signed certificates, you must use the `-C` (Trust Server Certificate) flag to prevent connection errors.
  Example test command: `sqlcmd -S "localhost\MSSQLSERVER2022" -E -C -Q "SELECT 1"`

## 🔒 Local-First & Data Privacy
- **Local-first:** Development runs entirely on a local stack (Qdrant, Redis, MinIO, MS SQL Server) via containers; cloud/Kubernetes is deferred to each engine's deployment-readiness sprint.
- **Data privacy:** Observability and model tooling must be self-hostable so enterprise data never leaves the environment; no data is sent to third-party managed services by default.
- **Governed by design:** Classification clearance, security context, and audit trails are enforced across ingestion, retrieval, and chat.

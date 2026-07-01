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

## 🔒 Local-First & Data Privacy
- **Local-first:** Development runs entirely on a local stack (Qdrant, Redis, MinIO, MS SQL Server) via containers; cloud/Kubernetes is deferred to each engine's deployment-readiness sprint.
- **Data privacy:** Observability and model tooling must be self-hostable so enterprise data never leaves the environment; no data is sent to third-party managed services by default.
- **Governed by design:** Classification clearance, security context, and audit trails are enforced across ingestion, retrieval, and chat.

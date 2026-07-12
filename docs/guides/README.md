# EK-RAG Product Guides

Welcome. This folder is the **complete, from-scratch documentation set** for the Enterprise Knowledge RAG System (EK-RAG). If you just cloned this repository and know nothing about the product, **start here and read in order.**

## What is EK-RAG (one paragraph)

EK-RAG is a self-hosted, local-first **Retrieval-Augmented Generation** platform. You point it at your enterprise documents; it converts them to a common format, extracts and indexes their meaning, and lets your users ask questions in a chat UI and get **grounded, cited answers** — without any data leaving your environment. It is built as five cooperating components:

| # | Component | Nickname | What it does |
|---|-----------|----------|--------------|
| 1 | **EKDC** | The Translator | Converts any file (PDF, Word, PowerPoint, images, audio, video…) into clean Markdown. |
| 2 | **EKIE** | The Factory | Ingests Markdown, extracts intelligence, chunks it, creates embeddings, publishes vectors. |
| 3 | **EKRE** | The Librarian | Answers "find me relevant knowledge" — query understanding, vector/keyword search, ranking, citations. |
| 4 | **EKCP** | The Brain | Runs the conversation: intent, memory, the LLM, and streaming chat with citations. |
| 5 | **Web UI** | The Face | The browser chat app your users actually see. |

Data flows left to right: **EKDC → EKIE → (Vector DB) → EKRE → EKCP → Web UI.**

## The guide set

Read these in order the first time:

1. **[Help Guide](01-help-guide.md)** — *What is all this?* Concepts, every component explained in plain English, the glossary, FAQ, and troubleshooting. **Read this first.**
2. **[Installation Guide](02-installation-guide.md)** — *How do I get it running from a fresh clone?* Every prerequisite, every install step, every config value, in order, for all five components.
3. **[User Guide](03-user-guide.md)** — *How do I actually use it?* For the people who add documents and chat with the assistant.
4. **[Admin Guide](04-admin-guide.md)** — *How do I run it in real life?* Configuration, security, secrets, backups, DSAR/GDPR purge, monitoring, scaling, and day-2 operations.
5. **[Deployment & Cleanup Guide](05-deployment-and-cleanup-guide.md)** — *Is this production-ready, and what do I remove?* An honest assessment of the deployment files (what exists, what follows best practice, and what forces you to run backend scripts by hand), a dev-vs-production configuration strategy, and a safe repository cleanup procedure + script.

## Deeper reference (existing engineering docs)

These guides summarize and operationalize the detailed engineering handbooks. For internals, see:

- [Master Architecture Blueprint](../master-architecture.md)
- [EKIE Handbook](../EKIE/EKIE-handbook.md) · [Deployment Guide](../EKIE/EKIE-Deployment-Guide.md) · [Help Guide](../EKIE/EKIE-Help_Guide.md)
- [EKRE Handbook](../EKRE/EKRE-handbook.md) · [Deployment Guide](../EKRE/EKRE-Deployment-Guide.md) · [Help Guide](../EKRE/EKRE-Help_Guide.md)
- [EKCP Handbook](../EKCP/EKCP-handbook.md) · [Deployment Guide](../EKCP/EKCP-Deployment-Guide.md) · [Help Guide](../EKCP/EKCP-Help_Guide.md)

## Ports at a glance (reference implementation)

| Service | Port | Notes |
|---|---|---|
| EKIE API | 8001 | Ingestion engine |
| EKRE API | 8002 | Retrieval engine |
| EKCP API | 8003 | Chat platform (the only API the Web UI talks to) |
| Web UI | 3001 (dev) | Defaults to 3001 to avoid the Langfuse (3000) clash |
| Qdrant | 6333 | Vector database |
| Redis | 6379 | Cache (used by Langfuse) |
| MinIO | 9005 / 9006 | Object storage API / console |
| Langfuse | 3000 | Observability UI |
| SQL Server | 1433 | Control plane (Windows-native, not in Docker) |
| Ollama | 11434 | Local LLM/embedding runtime (optional) |

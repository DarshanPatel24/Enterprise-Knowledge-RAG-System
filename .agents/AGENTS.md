# AGENTS

## Mission
Provide production-grade changes for EK-RAG while preserving strict engine boundaries, typed contracts, and enterprise traceability.

## Start Here
- Read [README.md](../README.md) for repo structure and contribution baseline.
- Read [docs/master-architecture.md](../docs/master-architecture.md) before any cross-service work.
- Read the engine handbook before changing that engine:
  - [docs/EKIE/EKIE-handbook.md](../docs/EKIE/EKIE-handbook.md)
  - [docs/EKRE/EKRE-handbook.md](../docs/EKRE/EKRE-handbook.md)
  - [docs/EKCP/EKCP-handbook.md](../docs/EKCP/EKCP-handbook.md)

## Non-Negotiable Architecture Rules
- No shared state between EKIE, EKRE, and EKCP.
- Inter-service communication must use REST APIs or event publishing only.
- Cross-service payloads must use Pydantic models defined in [packages/contracts](../packages/contracts).
- Respect ownership boundaries:
  - EKIE owns ingestion, document digital twins, and vector metadata schema.
  - EKRE owns retrieval logic, citation lineage, and saturation backpressure (HTTP 429).
  - EKCP owns conversation digital twins, memory governance, and LLM orchestration.

## Python Engineering Standards
- Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy.
- Strict typing everywhere; target mypy strict compliance.
- Use Pydantic v2 APIs (for example: model_validate, model_dump, Field).
- Never use bare except or catch generic Exception when a domain exception is available.
- No hardcoded credentials, URLs, or magic numbers; use environment-backed settings.
- Place service runtime settings in a centralized settings module (for example `services/<engine>/src/config/settings.py`).
- Keep user-editable defaults in configuration templates (for example `.env.example`) instead of source code constants.
- Use structured logging and include tenant_id and correlation_id where applicable.
- **Database Authentication**: Support Windows Authentication (Trusted Connection) for Microsoft SQL Server by prioritizing `Trusted_Connection=yes` in connection strings when configured by the user, rather than solely relying on username/password.

## Implementation Workflow For Agents
- Prefer local-first development and validation flows.
- Before coding, identify affected engine boundary and required contract updates.
- If payloads cross services, define/update the schema in [packages/contracts](../packages/contracts) first, then consume it in each service.
- Before adding a new constant, determine whether it is operationally tunable; if yes, add it to configuration instead of hardcoding.
- **Dynamic Configuration Overrides**: When allowing per-request overrides of global settings (e.g., model or provider selection), expose these as query parameters on the relevant REST API endpoints. Thread these parameters through immutable `WorkflowState` objects to dynamically alter engine policy logic for that specific request, without modifying global state.
- **Governed Registries & Overrides**: If a system uses a registry as a governed source of truth (e.g., `EmbeddingModelRegistry`), and a dynamic override is requested via the API, you must temporarily instantiate a localized registry seeded with the override parameters and pass it to the selector, rather than mutating the global registry or bypassing the selector entirely.
- **Provider Pluggability**: When adding support for new AI providers (e.g., HuggingFace alongside Ollama), implement them behind the engine's provider abstraction layer. Support dynamic selection via the API and ensure third-party package dependencies are lazily loaded so the default offline path remains unbloated.
- Keep edits minimal, explicit, and traceable.
- Add concise docstrings for public classes and public methods.

## Documentation Output Rules
- Use normative technical language in repository documentation.
- Do not add conversational filler, brainstorming text, or TODO-style placeholders in committed docs.
- For large architecture details, link to existing docs instead of duplicating them.

## Web UI Engineering Standards
- Web chat UI lives in `apps/web-ui/` (Next.js 14+ App Router, TypeScript strict, shadcn/ui).
- The UI is a REST and SSE client of the EKCP API gateway exclusively. No direct database, vector, cache, or engine internal access.
- All outbound requests must carry `X-Tenant-ID` and `X-Correlation-ID` headers.
- Configuration (API base URL, tenant ID, API key) is environment-backed; use `NEXT_PUBLIC_` env vars; never hardcode.
- Before any `apps/web-ui/` change, read master-architecture.md Section 13 and `.github/instructions/nextjs.instructions.md`.
- No external analytics, telemetry, or CDN dependencies at default configuration.
- Before adding UI features that cross the EKCP boundary, confirm the API contract exists (starts with EKCP-S0-5).

## Reference Implementation Stack
- Use LangChain and LangGraph for orchestration and agent workflows, behind engine-owned abstractions to preserve model independence.
- Standard infrastructure: Qdrant (vector DB), Redis (cache), MinIO (self-hosted, local object storage), Microsoft SQL Server (control plane; no PostgreSQL, no cloud).
- Web UI: Next.js 14+ App Router, TypeScript strict, shadcn/ui — local-first, self-hosted.
- Observability: Langfuse (self-hosted) plus OpenTelemetry; always include tenant_id and correlation_id in structured logs.
- Local-first and data privacy: default to self-hostable services so enterprise data never leaves the local environment; do not introduce third-party managed data services without approval.

# Enterprise Knowledge RAG System (EK-RAG)

Use this file for always-on guardrails. For expanded project guidance, see [../.agents/AGENTS.md](../.agents/AGENTS.md).

## Core Rules
- Keep EKIE, EKRE, and EKCP fully decoupled. No cross-engine database or memory access.
- Use REST APIs or events for inter-service communication.
- Define cross-service payloads in [../packages/contracts](../packages/contracts) using Pydantic v2 models.

## Python Standards
- Target Python 3.11+ with FastAPI and Pydantic v2.
- Require strict type hints for all arguments and return types.
- Use Pydantic v2 APIs such as model_validate, model_dump, and Field.
- Avoid bare except and generic Exception handling when domain exceptions are appropriate.
- Prefer structured logging with tenant_id and correlation_id context.

## Quality And Traceability
- No hardcoded credentials, URLs, or magic numbers; use configuration.
- Service configuration must be centralized in a settings module (for example `services/<engine>/src/config/settings.py`) and loaded from environment-backed files.
- User-adjustable operational values (timeouts, limits, feature toggles) must be exposed through configuration templates (for example `.env.example`) rather than code edits.
- Use descriptive names and brief comments that explain why, not what.
- Add concise docstrings for public classes and public methods.
- Keep documentation normative and avoid conversational filler or TODO placeholders.

## Enforcement Expectations
- Treat policy violations as blocking issues for implementation.
- Apply the same standards even when the prompt does not restate them.

## Reference Implementation Stack
- Orchestration and agents: LangChain and LangGraph, wrapped behind engine-owned abstractions so the core stays model-independent.
- Vector DB Qdrant, cache Redis, object storage MinIO (self-hosted, local), control plane Microsoft SQL Server (no PostgreSQL, no cloud).
- Observability: Langfuse (self-hosted) plus OpenTelemetry, with structured JSON logging carrying tenant_id and correlation_id.
- Local-first and data privacy: prefer self-hostable tooling; enterprise data must not leave the local environment by default.

## Web UI Standards
- Web chat UI lives in `apps/web-ui/` (Next.js 14+ App Router, TypeScript strict, shadcn/ui).
- The UI is a REST and SSE client of the EKCP API gateway only. No direct engine database access.
- Every request must inject `X-Tenant-ID` and `X-Correlation-ID` headers.
- No hardcoded API URLs, tenant IDs, or credentials; use `NEXT_PUBLIC_` environment variables.
- No external analytics, telemetry, or CDN dependencies at default configuration (local-first).
- Next.js/TypeScript conventions are enforced by `.github/instructions/nextjs.instructions.md` (`applyTo: apps/**/*.{ts,tsx}`).

## Canonical References
- [../README.md](../README.md)
- [../docs/master-architecture.md](../docs/master-architecture.md)
- [../docs/EKIE/EKIE-handbook.md](../docs/EKIE/EKIE-handbook.md)
- [../docs/EKRE/EKRE-handbook.md](../docs/EKRE/EKRE-handbook.md)
- [../docs/EKCP/EKCP-handbook.md](../docs/EKCP/EKCP-handbook.md)

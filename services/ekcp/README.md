# EKCP Service Scaffold

## Purpose
Chat orchestration engine implementation workspace.

## Standard Layout
1. `src/config` for settings and configuration models
2. `src/api` for FastAPI routers and request handlers
3. `src/domain` for orchestration domain logic
4. `tests` for service tests

## Notes
1. Enforce policy and audit requirements in governed execution paths.
2. Do not hardcode credentials, endpoints, or operational limits.
3. Reference stack: FastAPI, Pydantic v2, LangChain/LangGraph (behind abstractions), model-agnostic LLM gateway, Redis, Microsoft SQL Server.
4. Observability: Langfuse (self-hosted) plus OpenTelemetry; structured JSON logs with tenant_id and correlation_id.
5. Local-first and data privacy: prefer self-hostable models and tooling; do not send conversation data to managed third-party services by default.

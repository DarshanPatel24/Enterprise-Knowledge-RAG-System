# EKRE Service Scaffold

## Purpose
Retrieval engine implementation workspace.

## Standard Layout
1. `src/config` for settings and configuration models
2. `src/api` for FastAPI routers and request handlers
3. `src/domain` for retrieval domain logic
4. `tests` for service tests

## Notes
1. Enforce security-context validation before ranking paths.
2. Do not hardcode credentials, endpoints, or operational limits.
3. Reference stack: FastAPI, Pydantic v2, LangChain/LangGraph (behind abstractions), Qdrant, Redis, MinIO (local), Microsoft SQL Server.
4. Distance metric and embedding settings are inherited from EKIE metadata, never hardcoded.
5. Observability: Langfuse (self-hosted) plus OpenTelemetry; structured JSON logs with tenant_id and correlation_id.
6. Local-first and data privacy: run against the local container stack; do not send data to managed third-party services by default.

/**
 * Environment-backed configuration for the EK-RAG web UI.
 *
 * Every operational value is read from `NEXT_PUBLIC_*` environment variables.
 * No API URLs, tenant identifiers, ports, or credentials are hardcoded. Defaults
 * point at the local-first EKCP gateway and never at any external host.
 */

/** Base URL of the EKCP API gateway (single entry point for all engine traffic). */
export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_EKCP_URL ?? "http://localhost:8003";
}

/**
 * Tenant identifier injected as `X-Tenant-ID` on every request.
 *
 * In UI-S3 this becomes user-configurable via localStorage; for S0 it is
 * environment-backed so the health check can authenticate its origin tenant.
 */
export function getTenantId(): string {
  return process.env.NEXT_PUBLIC_EKCP_TENANT_ID ?? "";
}

/**
 * API key / gateway token sent as `Authorization: Bearer` on governed requests.
 *
 * Local-dev convenience only: seed it via `NEXT_PUBLIC_EKCP_API_KEY` so the app
 * works end-to-end without the Settings screen. For shared or production
 * deployments leave it empty and enter the key in-app so the secret never enters
 * the client bundle. localStorage always overrides this default.
 */
export function getApiKey(): string {
  return process.env.NEXT_PUBLIC_EKCP_API_KEY ?? "";
}

/**
 * User identifier carried in the security context on governed requests.
 *
 * Environment-backed for now; becomes user-configurable in UI-S3.
 */
export function getUserId(): string {
  return process.env.NEXT_PUBLIC_EKCP_USER_ID ?? "";
}

/**
 * Classification clearance carried in the security context.
 *
 * Environment-backed; defaults to the least-privileged level (`public`).
 */
export function getClearance(): string {
  return process.env.NEXT_PUBLIC_EKCP_CLEARANCE ?? "public";
}

/** Liveness endpoint path on the EKCP gateway. */
export const HEALTH_LIVE_PATH = "/health/live";

/** Readiness endpoint path on the EKCP gateway. */
export const HEALTH_READY_PATH = "/health/ready";

/** Streaming chat endpoint path on the EKCP gateway (SSE). */
export const CHAT_STREAM_PATH = "/chat/stream";

/**
 * Centralised EKCP API client.
 *
 * This is the ONLY module permitted to issue HTTP calls against the EKCP
 * gateway. Components and hooks call these functions; they never call `fetch`
 * directly. Every outbound request injects `X-Tenant-ID` (from configuration)
 * and a per-request `X-Correlation-ID` derived from `crypto.randomUUID()`.
 *
 * Local-first: all requests target the configured base URL (localhost by
 * default). No external hosts, analytics, or telemetry.
 */

import { CHAT_STREAM_PATH, HEALTH_LIVE_PATH } from "@/lib/config";
import { getSettingsSnapshot } from "@/lib/settings";
import type {
  ChatStreamRequest,
  Citation,
  ClassificationClearance,
  ConnectivityStatus,
  HealthResponse,
  SecurityContext,
  SseEvent,
} from "@/lib/api/types";

/**
 * Build the standard EKCP header set from the effective runtime settings.
 *
 * Injects `X-Tenant-ID`, a per-request `X-Correlation-ID`, and, when configured,
 * the gateway token as `Authorization: Bearer <key>` (the scheme the EKCP gateway
 * guard expects). Values come from the settings store (localStorage over env),
 * never hardcoded.
 */
export function buildHeaders(extra?: Record<string, string>): Headers {
  const settings = getSettingsSnapshot();
  const headers = new Headers({
    "Content-Type": "application/json",
    "X-Tenant-ID": settings.tenantId,
    "X-Correlation-ID": crypto.randomUUID(),
  });
  if (settings.apiKey) {
    headers.set("Authorization", `Bearer ${settings.apiKey}`);
  }
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      headers.set(key, value);
    }
  }
  return headers;
}

/**
 * Issue a request against an EKCP path with the standard header set.
 *
 * `path` must be a gateway-relative path (for example `/health/live`); the base
 * URL is resolved from configuration so no host is ever hardcoded.
 */
export async function ekcpFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const url = `${getSettingsSnapshot().apiBaseUrl}${path}`;
  return fetch(url, {
    ...init,
    headers: buildHeaders(
      init.headers instanceof Headers
        ? Object.fromEntries(init.headers.entries())
        : (init.headers as Record<string, string> | undefined),
    ),
  });
}

/**
 * Probe EKCP liveness and normalise the result into a `ConnectivityStatus`.
 *
 * Never throws: transport and non-2xx failures are captured so the UI can
 * render a connectivity indicator without an error boundary.
 */
export async function checkLiveness(): Promise<ConnectivityStatus> {
  try {
    const response = await ekcpFetch(HEALTH_LIVE_PATH, { method: "GET" });
    if (!response.ok) {
      return { state: "error", message: `EKCP returned HTTP ${response.status}` };
    }
    const body = (await response.json()) as HealthResponse;
    return { state: "ok", service: body.service, status: body.status };
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : "Unknown connection error";
    return { state: "error", message };
  }
}

/**
 * Build the security context carried on governed EKCP requests.
 *
 * Values come from the runtime settings store (never hardcoded); `tenant_id`
 * matches the `X-Tenant-ID` header so the EKCP ingress gate accepts the request.
 */
export function buildSecurityContext(): SecurityContext {
  const settings = getSettingsSnapshot();
  return {
    user_id: settings.userId,
    tenant_id: settings.tenantId,
    classification_clearance: settings.clearance,
  };
}

/**
 * Open a streaming chat request against EKCP `POST /chat/stream`.
 *
 * Returns the raw `Response`; callers consume the SSE body via `readSseStream`.
 * The `signal` allows the caller to abort an in-flight stream.
 */
export async function chatStream(
  message: string,
  options: { sessionId?: string; signal?: AbortSignal } = {},
): Promise<Response> {
  const body: ChatStreamRequest = {
    message,
    security_context: buildSecurityContext(),
    ...(options.sessionId ? { session_id: options.sessionId } : {}),
  };
  return ekcpFetch(CHAT_STREAM_PATH, {
    method: "POST",
    body: JSON.stringify(body),
    signal: options.signal,
  });
}

const CLEARANCE_LEVELS: ReadonlySet<string> = new Set([
  "public",
  "internal",
  "confidential",
  "restricted",
]);

/** Coerce an arbitrary clearance value to a known level, defaulting to `internal`. */
function toClearance(value: unknown): ClassificationClearance {
  const text = String(value ?? "").toLowerCase();
  return CLEARANCE_LEVELS.has(text)
    ? (text as ClassificationClearance)
    : "internal";
}

/** Map a raw `citation` frame payload to a typed `Citation`. */
function toCitation(data: Record<string, unknown>): Citation {
  const sourcePath = String(data.source_path ?? data.source ?? "");
  return {
    sourcePath,
    documentId: String(data.document_id ?? data.doc ?? ""),
    chunkId: String(data.chunk_id ?? data.chunk ?? ""),
    title: String(data.title ?? sourcePath.split(/[\\/]/).pop() ?? "Source"),
    confidence: Number(data.confidence ?? data.relevance_score ?? 0),
    clearance: toClearance(data.classification_clearance ?? data.clearance),
    explanation: String(data.explanation ?? ""),
  };
}

/** Parse a single raw SSE frame (`event: <type>\ndata: <json>`) into a typed event. */
export function parseSseBlock(block: string): SseEvent | null {
  let eventName = "";
  const dataLines: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }
  if (!eventName || dataLines.length === 0) {
    return null;
  }
  let data: Record<string, unknown>;
  try {
    data = JSON.parse(dataLines.join("\n")) as Record<string, unknown>;
  } catch {
    return null;
  }
  switch (eventName) {
    case "token":
      return { type: "token", text: String(data.text ?? "") };
    case "citation":
      return { type: "citation", citation: toCitation(data) };
    case "done":
      return {
        type: "done",
        done: {
          sessionId: String(data.session_id ?? ""),
          correlationId: String(data.correlation_id ?? ""),
          finishReason: String(data.finish_reason ?? ""),
          totalTokens: Number(data.total_tokens ?? 0),
          costEstimate: Number(data.cost_estimate ?? 0),
        },
      };
    case "error":
      return {
        type: "error",
        errorType: String(data.error_type ?? "error"),
        message: String(data.message ?? "Stream error"),
      };
    default:
      return null;
  }
}

/**
 * Consume an EKCP SSE response body as an async stream of typed events.
 *
 * Uses `fetch` + `ReadableStream` (never `EventSource`, which cannot carry the
 * required custom headers). Frames are delimited by a blank line (`\n\n`).
 */
export async function* readSseStream(response: Response): AsyncGenerator<SseEvent> {
  // The streaming endpoint always returns a body; guard for the typed union.
  if (!response.body) {
    throw new Error("EKCP chat stream returned an empty response body");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";
      for (const block of blocks) {
        const event = parseSseBlock(block);
        if (event) {
          yield event;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

---
applyTo: "apps/**/*.{ts,tsx}"
---

# Next.js And TypeScript Standards For EK-RAG Web UI

These rules apply to all TypeScript and TSX files under `apps/`. They define the conventions for structure, API communication, streaming, and state in the EK-RAG web chat UI (`apps/web-ui/`).

## Project Structure
- Use Next.js 14+ App Router. All pages go under `app/`; shared components go under `components/`; API client and hooks go under `lib/`.
- Do not put business logic in React components. Extract it into hooks (`lib/hooks/`) or server utilities (`lib/api/`).
- Keep `components/` flat and atomic: one component per file, named identically to the file (for example `CitationCard.tsx` exports `CitationCard`).

## TypeScript Standards
- Enable `strict: true` in `tsconfig.json`. Never disable or bypass strict mode for convenience.
- Declare explicit return types on all functions, hooks, and async server actions.
- Prefer `type` aliases for plain shapes; use `interface` only when extension is intended.
- Never use `any`. Use `unknown` with a narrowing guard when the type is genuinely unknown.
- Do not use non-null assertion (`!`) except where the value is structurally guaranteed and a comment explains why.

## Environment And Configuration
- Every configurable value (API base URL, default timeout, feature flags) must come from environment variables.
- Client-visible variables use the `NEXT_PUBLIC_` prefix; server-only secrets must not use this prefix.
- Provide a `.env.local.example` file listing all required variables with empty values and inline comments.
- Never hardcode `localhost`, port numbers, tenant identifiers, or API keys in source files.

```typescript
// Correct — environment-backed, never hardcoded.
const apiBase = process.env.NEXT_PUBLIC_EKCP_URL ?? "http://localhost:8003";
```

## EKCP API Client
- Centralise all EKCP HTTP calls in `lib/api/ekcp.ts`. No component or hook may call `fetch` against EKCP directly.
- Inject `X-Tenant-ID` and `X-Correlation-ID` on every outbound request. Derive `X-Correlation-ID` from `crypto.randomUUID()` per request; read `X-Tenant-ID` from configuration (never from user-supplied form input without sanitisation).
- Define typed response models using `type` aliases that mirror the `packages/contracts` Pydantic models. Do not share Python runtime code; replicate the shape in TypeScript.

```typescript
// Correct — explicit header injection on every call.
async function chatStream(payload: ChatRequest): Promise<Response> {
  return fetch(`${apiBase}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-ID": getTenantId(),
      "X-Correlation-ID": crypto.randomUUID(),
    },
    body: JSON.stringify(payload),
  });
}
```

## SSE Streaming Pattern
- Consume EKCP Server-Sent Events via `fetch` + `ReadableStream`; do not use `EventSource` (it does not support custom headers).
- Process SSE event types explicitly: `token` (append to response), `citation` (collect for card display), `done` (finalise state), `error` (surface error message and stop).
- Never start a new stream before the previous one is closed. Abort with `AbortController` on component unmount or new submission.

```typescript
// Correct SSE consumption pattern.
async function* readStream(response: Response): AsyncGenerator<SseEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";
    for (const block of lines) {
      const event = parseSseBlock(block);
      if (event) yield event;
    }
  }
}
```

## Component Conventions (shadcn/ui)
- Use shadcn/ui primitives as the base for all interactive elements. Do not create bespoke button, input, badge, or card components from scratch.
- Classification clearance badges must use semantically distinct, WCAG 2.1 AA contrast-compliant colours: public (green), internal (blue), confidential (amber), restricted (red).
- Avoid inline styles. Use Tailwind utility classes only; define custom design tokens in `tailwind.config.ts`.

## State Management
- Prefer React built-ins (`useState`, `useReducer`, `useContext`) for UI state. Do not add a global state library unless the complexity clearly justifies it.
- Streaming state (current partial response, citation buffer, streaming flag) lives in a dedicated `useChatStream` hook, not in a page component.
- Session and configuration values that must survive page reload are persisted to `localStorage` only. Never send configuration values to a server.

## Data Privacy And Local-First
- Zero external HTTP calls at default configuration. Every `fetch` call must target the configured API base URL (localhost by default).
- Do not import or configure any analytics, error-reporting, or crash-reporting SDK that transmits data outside the local environment.
- If error boundaries or logging are needed, log to the browser console only.

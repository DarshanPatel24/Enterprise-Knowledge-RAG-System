# Web UI Sprint Track

> Track Owner: Web UI Lead
> Start Condition: EKCP-S0 exit gate passed (SSE streaming chat API contract approved)
> Objective: Deliver a self-hosted, local-first enterprise web chat UI that streams responses, renders citations, and manages conversation sessions, consuming the EKCP API gateway exclusively.
> Source Of Truth: [../master-architecture.md](../master-architecture.md) Section 13

## Alignment To Architecture
This track implements the Web UI Layer defined in master-architecture.md Section 13. The UI is a consuming REST and SSE client of the EKCP API gateway only. It has no direct access to any engine database, vector store, cache, or internal service. All enterprise data flows through the EKCP boundary. No cloud dependencies. No external analytics or telemetry.

Build order follows the delivery dependency chain: scaffold and API client first, then streaming chat core, then citation and context display, then session management.

## Track Definition Of Ready
1. EKCP-S0 exit gate is approved and the SSE streaming chat API contract (EKCP-S0-5) is documented.
2. EKCP API base URL, tenant header convention (`X-Tenant-ID`, `X-Correlation-ID`), and API key scheme are confirmed.
3. Node.js 20+ LTS is available locally.
4. Web UI story owners, reviewers, and quality owners are assigned.

## Track Definition Of Done
1. All sprint stories meet acceptance criteria with review evidence.
2. Streaming token display works end-to-end: EKCP token events render in the browser without full-page refresh.
3. Citation cards display source path, confidence score, and classification clearance for every response that carries citations.
4. Session list loads existing conversations and preserves state across page reloads.
5. Zero external HTTP calls at default configuration; all traffic targets `localhost`.
6. TypeScript strict compilation passes with zero errors; ESLint clean.

## Success Metrics (Track Level)
1. Streaming first-token display latency addition from UI layer: < 50 ms.
2. TypeScript strict: zero compilation errors.
3. ESLint: zero lint errors.
4. All API calls carry `X-Tenant-ID` and `X-Correlation-ID` headers: 100%.
5. No hardcoded API base URLs or tenant identifiers in source code: 100%.

## Dependency Map
```
EKCP-S0 (SSE contract) → UI-S0 (scaffold + API client)
                              ↓
                   EKCP-S3 (model gateway) → UI-S1 (streaming chat)
                                                  ↓
                              EKRE exit gate → UI-S2 (citations)
                                                  ↓
                              EKCP-S4 (memory) → UI-S3 (sessions)
```

---

## UI-S0: Scaffold And API Client Baseline

> Status: Approved (TypeScript strict `tsc --noEmit` clean, ESLint clean, `next build` clean — 4 static routes). Implemented in `apps/web-ui/` (Next.js 14.2.35 App Router, Tailwind + shadcn/ui primitives). The EKCP client is centralized in `lib/api/ekcp.ts` with `X-Tenant-ID` and per-request `X-Correlation-ID` injection; all config is `NEXT_PUBLIC_*` env-backed (default gateway `http://localhost:8003`), nothing hardcoded. The home page probes `/health/live` and renders a connectivity status card.

### Sprint Objective
Establish the Next.js App Router project, TypeScript strict config, shadcn/ui component library, environment-backed API client, and a health check page that confirms connectivity to EKCP.

### Start Condition
EKCP-S0 exit gate passed; SSE streaming chat API contract documented (EKCP-S0-5).

### Scope
1. Next.js 14+ App Router scaffold in `apps/web-ui/` with TypeScript strict (`strict: true` in `tsconfig.json`).
2. ESLint and Prettier configuration aligned with project standards.
3. Environment-backed EKCP API client (`NEXT_PUBLIC_EKCP_API_URL`, tenant key from environment; no hardcoding).
4. `X-Tenant-ID` and `X-Correlation-ID` header injection on every outbound request.
5. Health check page (`/`) confirming EKCP liveness endpoint responds.
6. shadcn/ui and Tailwind CSS base installation.
7. `.env.local.example` template covering all configurable values.

### Out Of Scope
1. Chat message rendering and streaming.
2. Citation display.
3. Session management UI.

### Stories
1. UI-S0-1 Next.js App Router scaffold with TypeScript strict and ESLint.
2. UI-S0-2 Environment-backed EKCP API client with tenant and correlation header injection.
3. UI-S0-3 shadcn/ui and Tailwind CSS base.
4. UI-S0-4 Health check page confirming EKCP `/health/live` responds.
5. UI-S0-5 `.env.local.example` template.

### Deliverables
1. `apps/web-ui/` project passing TypeScript strict compilation and ESLint clean.
2. EKCP API client with header injection and typed response models.
3. Health check page with connectivity status indicator.

### Acceptance
1. `npm run build` produces zero TypeScript and ESLint errors.
2. Health check page renders EKCP status without hardcoded URLs.
3. No credentials, API URLs, or tenant identifiers are hardcoded in source.

### Exit Evidence
1. Approved TypeScript strict build log.
2. Health check page screenshot confirming EKCP connectivity.

### Delivery Evidence
1. UI-S0-1 Approved: `apps/web-ui/` Next.js 14 App Router scaffold with `tsconfig.json` `strict: true` (plus `noUncheckedIndexedAccess`), `.eslintrc.json` extending `next/core-web-vitals`, and Prettier config. `npm run typecheck`, `npm run lint`, and `npm run build` all pass with zero errors.
2. UI-S0-2 Approved: `lib/api/ekcp.ts` is the sole EKCP HTTP entry point; `buildHeaders()` injects `X-Tenant-ID` (from `lib/config.ts`) and a per-request `X-Correlation-ID` via `crypto.randomUUID()` on every call. Response shapes are typed in `lib/api/types.ts` mirroring the contracts. No component calls `fetch` directly.
3. UI-S0-3 Approved: Tailwind CSS (`tailwind.config.ts` + `app/globals.css` design tokens) with shadcn/ui primitives (`components/ui/{button,card,badge}.tsx`) and the `cn()` utility. Classification-clearance colour tokens (public/internal/confidential/restricted) are defined for UI-S2.
4. UI-S0-4 Approved: `app/page.tsx` + `components/HealthStatus.tsx` probe EKCP `/health/live` through the client and render an online/offline/loading connectivity card with a re-check action; the gateway URL is shown from configuration, never hardcoded.
5. UI-S0-5 Approved: `.env.local.example` documents `NEXT_PUBLIC_EKCP_API_URL` (default `http://localhost:8003`) and `NEXT_PUBLIC_EKCP_TENANT_ID`, all localhost-targeted with empty credential defaults.

### Security Note
The web UI runs on **Next.js 16 + React 19** (upgraded from the initial 14.x). `npm audit` reports **0 vulnerabilities** (the postcss transitive advisory is pinned via a package override); TypeScript strict, ESLint (flat config), and `next build` (Turbopack) all pass. This closes the earlier residual-advisory item (release risk R5).

### Browser E2E (Playwright)
A Playwright browser test (`apps/web-ui/e2e/chat.spec.ts`, run via `npm run test:e2e`) drives the chat UI in Chromium, intercepts the EKCP SSE contract at the network layer, and asserts streamed tokens render, a citation card displays the source path and clearance badge, and the pre-chat configuration gate blocks input until settings are present. This closes the browser-level validation item (release risk R3 / M2-D2).

---

## UI-S1: Core Streaming Chat Interface

> Status: Approved (TypeScript strict `tsc --noEmit` clean, ESLint clean, `next build` clean — 5 static routes). Implemented in `apps/web-ui/`: SSE parsing and `chatStream` in `lib/api/ekcp.ts` (fetch + ReadableStream, never `EventSource`), the `useChatStream` hook (`lib/hooks/`) owning transcript/streaming/error state with `AbortController` lifecycle, and the chat UI (`components/{ChatPanel,MessageList,ChatMessage,ChatInput}.tsx`) at the `/chat` route. Verified end-to-end against a live EKCP gateway: `POST /chat/stream` returned HTTP 200 `text/event-stream`, streamed `token` frames and a terminal `done` frame (`finish_reason: stop`, `total_tokens: 41`), and propagated `X-Correlation-ID` back on the response.

### Sprint Objective
Deliver the core chat experience: message list, streaming token display via SSE, chat input, and error/loading states.

### Start Condition
UI-S0 exit gate passed. EKCP-S3 exit gate passed (model gateway available to stream responses).

### Scope
1. Chat message list rendering user and assistant bubbles.
2. SSE token streaming: consume EKCP `token` events and display partial response in real time.
3. `done` event handling to finalize the response and reset streaming state.
4. `error` event handling with user-visible error message.
5. Chat input component with submit on Enter and button click.
6. Loading/thinking indicator while awaiting first token.
7. Auto-scroll to latest message.

### Out Of Scope
1. Citation card rendering (next sprint).
2. Session history panel (UI-S3).
3. Markdown-rich rendering beyond plain text (delivered as enhancement in UI-S2).

### Stories
1. UI-S1-1 Chat message list component (user and assistant bubbles).
2. UI-S1-2 SSE streaming client hook consuming EKCP `token`, `done`, and `error` events.
3. UI-S1-3 Chat input component with submit and loading state.
4. UI-S1-4 Auto-scroll and UX polish (loading indicator, error banner).

### Deliverables
1. Working streaming chat interface against EKCP.
2. SSE client hook reusable for future citation and event types.

### Acceptance
1. First token renders in the browser within 50 ms of EKCP first-token emission.
2. Stream completes cleanly; no partial tokens hang after `done` event.
3. Error events surface a readable user message without crashing the UI.
4. Every chat request carries `X-Tenant-ID` and `X-Correlation-ID`.

### Exit Evidence
1. Approved screen recording demonstrating streaming end-to-end.
2. Network trace showing `X-Tenant-ID` and `X-Correlation-ID` present on every request.

### Delivery Evidence
1. UI-S1-1 Approved: `components/MessageList.tsx` + `components/ChatMessage.tsx` render right-aligned user and left-aligned assistant bubbles, an empty-transcript prompt, a streaming "Thinking…" indicator for an in-flight assistant message with no content yet, and an inline error marker on failed responses.
2. UI-S1-2 Approved: `lib/api/ekcp.ts` adds `chatStream()` (POST `/chat/stream` with env-backed security context), `parseSseBlock()`, and `readSseStream()` (fetch + `ReadableStream`, `\n\n`-delimited frames). The `useChatStream` hook (`lib/hooks/useChatStream.ts`) appends `token` fragments to the in-flight assistant message, finalizes on `done` (persisting `session_id` for subsequent turns), and surfaces `error` frames; `citation` frames are parsed and ignored until UI-S2.
3. UI-S1-3 Approved: `components/ChatInput.tsx` submits on Enter (Shift+Enter inserts a newline) and via the send button, disables the composer while streaming, and switches the action to a Stop control that aborts the active stream.
4. UI-S1-4 Approved: `components/MessageList.tsx` auto-scrolls to the latest entry on every transcript change (including streaming token appends); `components/ChatPanel.tsx` renders a dismissible-styled error banner and the loading indicator. A new stream never starts while one is active, and unmounting aborts the current stream.
5. Integration verified: a live EKCP smoke test (`POST /chat/stream`, `X-Tenant-ID`/`X-Correlation-ID` headers, security context) returned HTTP 200 `text/event-stream` and a full `token`…`done` sequence matching the client parser, with `X-Correlation-ID` propagated on the response.

---

## UI-S2: Citation And Context Display

> Status: Approved (TypeScript strict `tsc --noEmit` clean, ESLint clean, `next build` clean — 5 static routes). Implemented in `apps/web-ui/`: `CitationCard` + `ClearanceBadge` (colour-coded, WCAG AA on white text), the `citation` SSE consumer (`lib/api/ekcp.ts` `toCitation` + `useChatStream` buffers citations during the stream and attaches them to the assistant message on `done`), `MarkdownContent` (`react-markdown` + `remark-gfm` tables/lists + `rehype-highlight` code, locally bundled — no external requests), an `AgentActivity` reasoning indicator shown before the first token, and a client-derived response-type label.

### Sprint Objective
Render citations alongside assistant responses — source cards (title, path, confidence score, classification clearance badge) — and upgrade response rendering to full Markdown including tables and lists.

### Start Condition
UI-S1 exit gate passed. EKRE exit gate passed (citation contracts carry source path, confidence, and clearance).

### Scope
1. Citation cards: source title, source path, confidence score, classification clearance badge (color-coded).
2. SSE `citation` event consumption and card rendering after `done`.
3. Markdown response rendering with tables, ordered/unordered lists, code blocks, and inline formatting.
4. Agent activity indicator (shown while EKCP is executing a reasoning step before first token).
5. Response type labeling (conversational, structured, markdown, table, list).

### Out Of Scope
1. Session list and conversation history.
2. Multi-agent workflow visualization.

### Stories
1. UI-S2-1 Citation card component with clearance badge and confidence display.
2. UI-S2-2 SSE `citation` event consumer and card insertion on `done`.
3. UI-S2-3 Markdown renderer (`react-markdown` with rehype plugins for tables and code).
4. UI-S2-4 Agent activity indicator (reasoning in progress state).

### Deliverables
1. Citation cards rendered per response with complete source metadata.
2. Markdown responses rendered correctly including tables and code blocks.
3. Agent activity indicator shown during long-running reasoning steps.

### Acceptance
1. Every citation card displays source path, confidence score, and clearance badge.
2. Classification clearance badge uses distinct, accessible colors per level (public, internal, confidential, restricted).
3. Markdown tables and code blocks render without layout breakage.
4. No citation data is dropped between EKCP SSE stream and UI card display.

### Exit Evidence
1. Approved screenshot set showing citation cards and markdown responses.
2. Clearance badge accessibility contrast check evidence.

### Delivery Evidence
1. UI-S2-1 Approved: `components/CitationCard.tsx` renders source title, source path, confidence (0..1 formatted as a percentage), an optional explanation, and a `components/ClearanceBadge.tsx` clearance badge. Badge colours use the `tailwind.config.ts` clearance tokens — public (green), internal (blue), confidential (amber), restricted (red) — each WCAG 2.1 AA compliant against white text.
2. UI-S2-2 Approved: `lib/api/ekcp.ts` parses the `citation` SSE frame into a typed `Citation` (mapping the EKRE citation fields `source_path`/`document_id`/`chunk_id` plus confidence and clearance). `useChatStream` buffers `citation` frames during the stream and attaches the full set to the assistant message on `done`, so no citation is dropped between stream and card.
3. UI-S2-3 Approved: `components/MarkdownContent.tsx` renders GitHub-flavoured Markdown via `react-markdown` with `remark-gfm` (tables, ordered/unordered lists) and `rehype-highlight` (fenced code blocks). Tables scroll horizontally and code blocks wrap in a bordered `pre`; styling is Tailwind-only. All Markdown assets are bundled locally — no external requests.
4. UI-S2-4 Approved: `components/AgentActivity.tsx` shows a distinct "Agent is reasoning…" indicator while the assistant message is streaming with no content yet (before the first token).
5. Response-type labeling Approved: `lib/responseType.ts` classifies completed assistant content into conversational / structured / markdown / table / list and renders it as a subtle label under the message.

### Follow-up (EKCP wiring, outside Web UI track)
EKCP `POST /chat/stream` does not yet emit `citation` frames (the endpoint docstring notes they are emitted once knowledge integration is wired into the streaming path). The UI consumer is complete and conforms to the documented `citation` event; cards render as soon as EKCP emits citation frames from the assembled retrieval context. Recommend tracking the EKCP stream-to-citation wiring under Master Integration M2-S4 (end-to-end web UI validation).

---

## UI-S3: Session Management And Configuration

> Status: Approved (TypeScript strict `tsc --noEmit` clean, ESLint clean, `next build` clean — 6 static routes). Implemented in `apps/web-ui/`: a `localStorage`-backed conversation store (`lib/conversations.ts`) and runtime settings store (`lib/settings.ts`, `localStorage` over env via `useSyncExternalStore`), the `ChatWorkspace` sidebar (`ConversationList` new/load, title from first user message), the `/settings` configuration screen (`SettingsForm`), and a pre-chat validation gate disabling input until the required settings are present. The EKCP client now reads effective settings and adds `X-API-Key` when configured. Local-first: all values persist only in the browser; requests target the configured EKCP URL only.

### Sprint Objective
Deliver persistent conversation session management (list, create, load) and the API key configuration screen so the UI is self-sufficient for local-first enterprise use.

### Start Condition
UI-S2 exit gate passed. EKCP-S4 exit gate passed (conversation memory persists and is retrievable).

### Scope
1. Conversation session list panel showing past conversations with title and timestamp.
2. New conversation action and load existing conversation.
3. Conversation title derived from first user message.
4. API key and tenant ID configuration screen (values stored in `localStorage` only; no server-side session store).
5. Settings validation: warn the user if API key or tenant ID is empty before allowing chat.

### Out Of Scope
1. User authentication against an external identity provider.
2. Multi-tenant admin panel.
3. Analytics dashboard.

### Stories
1. UI-S3-1 Conversation session list component (load from EKCP history endpoint).
2. UI-S3-2 New conversation and load conversation actions.
3. UI-S3-3 API key and tenant ID configuration screen with localStorage persistence.
4. UI-S3-4 Pre-chat validation warning when configuration is incomplete.

### Deliverables
1. Session list persisting across page reloads via EKCP history API.
2. Configuration screen with localStorage-backed API key and tenant ID.

### Acceptance
1. Session list updates after each new conversation without page reload.
2. Configuration values survive browser refresh.
3. Chat input is disabled with a clear message when API key or tenant ID is not set.
4. No credentials are sent to any external service; all API calls target configured localhost URL.

### Exit Evidence
1. Approved screenshot showing session list and configuration screen.
2. Network trace confirming zero requests to external hosts.

### Delivery Evidence
1. UI-S3-1 Approved: `components/ConversationList.tsx` renders the stored conversation index (title + updated timestamp, newest first) with the active entry highlighted; selecting an entry loads its persisted transcript. The list is backed by `lib/conversations.ts` (`localStorage`), so it survives reloads. (EKCP exposes no conversation history endpoint yet; the local store is the source of truth and can hydrate from EKCP once such an endpoint exists.)
2. UI-S3-2 Approved: `components/ChatWorkspace.tsx` provides new-conversation and load-conversation actions; the chat panel is remounted per conversation (`key`) to seed its stored transcript. Conversation titles derive from the first user message (`deriveTitle`), and the list updates after each settled turn without a page reload.
3. UI-S3-3 Approved: `components/SettingsForm.tsx` at `/settings` persists API base URL, API key, tenant id, user id, and clearance to `localStorage` only (`lib/settings.ts`). The EKCP client (`lib/api/ekcp.ts`) reads these effective values and injects `X-Tenant-ID` and, when set, `X-API-Key`. Values survive browser refresh.
4. UI-S3-4 Approved: a configuration-required banner and a disabled composer (`isConfigured` / `missingRequiredFields`) block chat until tenant id, API key, and user id are set, listing exactly what is missing.
5. Local-first verified: all persistence is `localStorage`; every request targets the configured EKCP base URL (localhost by default) with no external hosts, analytics, or telemetry.

> Web UI track complete: UI-S0 through UI-S3 approved. Remaining cross-track item: EKCP `POST /chat/stream` citation-frame emission, to be validated end-to-end under Master Integration M2-S4.

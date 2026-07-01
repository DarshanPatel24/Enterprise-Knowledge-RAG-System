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

---

## UI-S1: Core Streaming Chat Interface

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

---

## UI-S2: Citation And Context Display

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

---

## UI-S3: Session Management And Configuration

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

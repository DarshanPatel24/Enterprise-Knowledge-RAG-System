# EK-RAG Web UI

Local-first enterprise knowledge chat interface for the EK-RAG platform. This app
is a REST and SSE client of the **EKCP API gateway only** (default
`http://localhost:8003`). It has no direct access to any engine database, vector
store, cache, or internal service, and makes zero external HTTP calls at default
configuration.

## Stack
- Next.js 16 App Router, React 19, TypeScript strict
- Tailwind CSS + shadcn/ui primitives
- SSE streaming via `fetch` + `ReadableStream` (no `EventSource`)
- ESLint 9 flat config; Playwright browser E2E

## Getting started
1. Copy the environment template and fill values:
   ```
   cp .env.local.example .env.local
   ```
2. Install dependencies:
   ```
   npm install
   ```
3. Run the dev server (EKCP must be running on the configured URL):
   ```
   npm run dev
   ```
   The dev server listens on port **3001** (avoids a clash with Langfuse on 3000).
4. Open the app; the home page confirms EKCP connectivity.

## Scripts
- `npm run dev` — start the development server (port 3001).
- `npm run build` — production build (Turbopack).
- `npm run start` — serve the production build (port 3001).
- `npm run lint` — ESLint (flat config).
- `npm run typecheck` — `tsc --noEmit`.
- `npm run test:e2e` — Playwright browser E2E.

## Conventions
See [../../.github/instructions/nextjs.instructions.md](../../.github/instructions/nextjs.instructions.md).
All EKCP HTTP calls are centralised in `lib/api/ekcp.ts`; every request injects
`X-Tenant-ID` and a per-request `X-Correlation-ID`.

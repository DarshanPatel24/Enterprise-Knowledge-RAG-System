# EK-RAG Web UI

Local-first enterprise knowledge chat interface for the EK-RAG platform. This app
is a REST and SSE client of the **EKCP API gateway only** (default
`http://localhost:8003`). It has no direct access to any engine database, vector
store, cache, or internal service, and makes zero external HTTP calls at default
configuration.

## Stack
- Next.js 14 App Router, TypeScript strict
- Tailwind CSS + shadcn/ui primitives
- SSE streaming via `fetch` + `ReadableStream` (no `EventSource`)

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
4. Open the app; the home page confirms EKCP connectivity.

## Scripts
- `npm run dev` — start the development server.
- `npm run build` — production build (TypeScript strict + ESLint gate).
- `npm run lint` — ESLint.
- `npm run typecheck` — `tsc --noEmit`.

## Conventions
See [../../.github/instructions/nextjs.instructions.md](../../.github/instructions/nextjs.instructions.md).
All EKCP HTTP calls are centralised in `lib/api/ekcp.ts`; every request injects
`X-Tenant-ID` and a per-request `X-Correlation-ID`.

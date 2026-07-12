# Web UI Deployment Guide

**Audience:** Engineers, DevOps, and platform operators.
**Component:** `apps/web-ui/` — EK-RAG local-first enterprise chat UI.
**Last updated:** 2026-07-08

---

## Table of Contents

1. [Overview and Architecture Placement](#1-overview-and-architecture-placement)
2. [Prerequisites](#2-prerequisites)
3. [Configuration Reference](#3-configuration-reference)
4. [Local Development](#4-local-development)
5. [Production Build and Run](#5-production-build-and-run)
6. [Whole-Product Bring-Up Order](#6-whole-product-bring-up-order)
7. [Connectivity Verification Checklist](#7-connectivity-verification-checklist)
8. [Production Hardening](#8-production-hardening)
9. [Reverse Proxy and TLS](#9-reverse-proxy-and-tls)
10. [Upgrade and Rollback](#10-upgrade-and-rollback)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview and Architecture Placement

The web UI is the browser-facing layer of EK-RAG. It is a **REST and SSE client of the EKCP API gateway only** (default `http://localhost:8003`). It has:

- **No** direct access to any engine database, vector store (Qdrant), cache (Redis), object store (MinIO), or control plane (SQL Server).
- **No** external HTTP calls at default configuration — no analytics, telemetry, CDN, or cloud services.

All enterprise data flows through the EKCP boundary. The UI consumes exactly three EKCP endpoints:

| Purpose | EKCP path | Method |
|---|---|---|
| Liveness probe (connectivity card) | `/health/live` | GET |
| Readiness probe | `/health/ready` | GET |
| Streaming chat | `/chat/stream` | POST (SSE response) |

Every outbound request injects `X-Tenant-ID`, a per-request `X-Correlation-ID`, and, when an API key is configured, `Authorization: Bearer <key>`.

**Stack:** Next.js App Router (pinned in `package.json`; currently 16.x), React 19, TypeScript strict, Tailwind CSS + shadcn/ui primitives. SSE is consumed with `fetch` + `ReadableStream` (never `EventSource`).

---

## 2. Prerequisites

### 2.1 Software

| Software | Version | Notes |
|---|---|---|
| Node.js | 20+ LTS | https://nodejs.org/ |
| npm | Bundled with Node 20+ | Lockfile is `package-lock.json` |
| A running EKCP gateway | Current | The UI's only backend dependency (default `http://localhost:8003`) |

### 2.2 Hardware

The UI itself is lightweight (a Node process serving static assets and a thin server runtime). Minimums: 2 CPU cores, 2 GB RAM, 1 GB disk. The heavy compute (embeddings, retrieval, reranking, generation) lives in the engines, not the UI.

### 2.3 Network

All traffic targets `localhost` by default. The only required reachability is **browser → web UI** and **web UI → EKCP**. No outbound internet access is required at runtime; `npm install` needs registry access once to fetch dependencies.

---

## 3. Configuration Reference

### 3.1 Build-time environment (`.env.local`)

Copy the template and fill values. Never commit `.env.local`.

```powershell
Copy-Item apps/web-ui/.env.local.example apps/web-ui/.env.local
```

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_EKCP_URL` | `http://localhost:8003` | Base URL of the EKCP gateway (the single entry point). Must point at a reachable EKCP instance. |
| `NEXT_PUBLIC_EKCP_TENANT_ID` | *(empty)* | Tenant id injected as `X-Tenant-ID`. Provide a real tenant id. |
| `NEXT_PUBLIC_EKCP_USER_ID` | *(empty)* | User id carried in the security context on governed requests. |
| `NEXT_PUBLIC_EKCP_CLEARANCE` | `public` | Classification clearance: `public` \| `internal` \| `confidential` \| `restricted`. |

> All client-visible values use the `NEXT_PUBLIC_` prefix. No API URLs, tenant ids, ports, or credentials are hardcoded in source.

### 3.2 Runtime settings (per-browser, `localStorage`)

The in-app **Settings** screen (`/settings`) overrides the build-time defaults and persists to the browser's `localStorage` only (key `ekrag.settings.v1`). These values are never sent anywhere except the configured EKCP gateway.

| Setting | Required for chat | Notes |
|---|---|---|
| API base URL | — | Defaults to `NEXT_PUBLIC_EKCP_URL`. |
| Tenant ID | Yes | Sent as `X-Tenant-ID`; must match the security-context tenant. |
| User ID | Yes | Carried in the security context. |
| API key | Yes | Sent as `Authorization: Bearer <key>`; the scheme the EKCP gateway guard expects. |
| Clearance | — | Defaults to `public` (least privilege). |

Chat input is disabled until Tenant ID, User ID, and API key are set.

---

## 4. Local Development

```powershell
Push-Location apps/web-ui
npm install
npm run dev            # starts the dev server on http://localhost:3001
Pop-Location
```

Open `http://localhost:3001`. The home page probes EKCP `/health/live` and renders a connectivity status card. EKCP must be running on the configured URL.

### Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Development server with hot reload. |
| `npm run build` | Production build (TypeScript strict + ESLint gate). |
| `npm run start` | Serve the production build. |
| `npm run lint` | ESLint. |
| `npm run typecheck` | `tsc --noEmit`. |
| `npm run test:e2e` | Playwright browser end-to-end tests. |

---

## 5. Production Build and Run

```powershell
Push-Location apps/web-ui
npm ci                 # clean, lockfile-exact install
npm run build          # fails on any type or lint error
npm run start          # serves on port 3001 by default
Pop-Location
```

- **Port:** default `3001` (set in `package.json`; port `3000` is used by the local Langfuse container). Override with `npm run start -- -p 8080` or the `PORT` environment variable.
- **Environment:** `.env.local` (or real environment variables) must be present at build time — `NEXT_PUBLIC_*` values are inlined during `npm run build`. To change the EKCP URL for a built artifact, rebuild or have users override it via the Settings screen at runtime.
- **Process management:** run `npm run start` under a supervisor (for example `pm2`, a Windows service, or a systemd unit) so it restarts on failure.

---

## 6. Whole-Product Bring-Up Order

The UI is the last layer to start. Bring the platform up bottom-up so each layer's dependency is ready:

1. **Infrastructure** — Qdrant (vectors), Redis (cache), MinIO (objects), SQL Server (control plane). See the root `docker-compose.local.yml` if you self-host these with containers; otherwise start your local instances.
2. **EKIE** (ingestion) — ingest and publish vectors to the shared Qdrant collection. See [../EKIE/EKIE-Deployment-Guide.md](../EKIE/EKIE-Deployment-Guide.md). API on port **8001**.
3. **EKRE** (retrieval) — reads the vectors EKIE published; produces the retrieval context package. API on port **8002**.
4. **EKCP** (control plane / gateway) — the UI's only dependency; orchestrates EKRE + generation and exposes `/health/*` and `/chat/stream`. API on port **8003**.
5. **Web UI** — build and start (`apps/web-ui`); point `NEXT_PUBLIC_EKCP_URL` at the EKCP gateway. Default port **3001** (port 3000 is the local Langfuse UI).

> Minimum viable chat requires only EKCP (which internally depends on EKRE + a generation model). EKIE must have published data for retrieval to return citations.

---

## 7. Connectivity Verification Checklist

After starting the UI:

- [ ] `http://localhost:3001` loads and the home page renders the connectivity card.
- [ ] The card shows **connected** (green) with the EKCP service name and status — confirms `GET /health/live` succeeds.
- [ ] In **Settings**, Tenant ID, User ID, and API key are set; the chat input becomes enabled.
- [ ] Sending a message streams tokens incrementally (no full-page refresh).
- [ ] A **stage progress indicator** appears while the answer is being prepared, cycling through *understanding → retrieving → reranking → reasoning → generating* (delivered as SSE `stage` events).
- [ ] Responses that carry sources render **citation cards** with source path, score, and a clearance badge.
- [ ] Browser dev tools **Network** tab shows requests only to the EKCP base URL — no external hosts.
- [ ] Every EKCP request carries `X-Tenant-ID` and `X-Correlation-ID` headers.

---

## 8. Production Hardening

- **Serve over HTTPS.** Terminate TLS at a reverse proxy (see §9); never expose the UI or EKCP over plain HTTP outside localhost.
- **Do not bake secrets into the build.** The API key is a per-user runtime value entered in Settings (stored in `localStorage`), not a `NEXT_PUBLIC_*` build variable. Rotate keys on the EKCP side.
- **Powered-By header is disabled** (`poweredByHeader: false`) and there is no telemetry, no external image domains, and no analytics by design — keep it that way.
- **CORS:** EKCP must allow the UI origin for browser requests. Restrict EKCP CORS to the exact UI origin(s); do not use `*` in production.
- **Clearance is not a trust boundary in the browser.** The UI sends the user-selected clearance/tenant; EKCP (and EKRE's signed-context verification, when enabled) is responsible for authorizing them. Do not treat the UI's clearance selector as an access-control decision point.
- **Content Security Policy:** add a strict CSP at the proxy that permits `connect-src` only to the EKCP origin and `self`, and disallows external script/style/img sources (the app bundles highlight.js and markdown rendering locally — no external requests are needed).

---

## 9. Reverse Proxy and TLS

Front the Node server with a reverse proxy (nginx, Caddy, IIS ARR) that:

- Terminates TLS and forwards to `http://127.0.0.1:3001`.
- Forwards `Upgrade`/streaming correctly and **does not buffer** the `/chat/stream` response, so Server-Sent Events flush token-by-token. For nginx set `proxy_buffering off;` on the chat route; for Caddy streaming works by default.
- Sets security headers (HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, a strict CSP).

If EKCP is also proxied, keep the UI's `NEXT_PUBLIC_EKCP_URL` (or the runtime Settings API base URL) pointing at the **externally reachable** EKCP URL the browser can resolve.

---

## 10. Upgrade and Rollback

- **Upgrade:** pull the new revision, `npm ci`, `npm run build`, then restart `npm run start`. The build gate (`tsc` strict + ESLint) blocks a broken release.
- **Rollback:** redeploy the previous build artifact / git revision and restart. The UI is stateless on the server; user conversations and settings live in each browser's `localStorage` and are unaffected by a server rollback.
- **Cache busting:** Next.js fingerprints static assets, so browsers pick up new assets automatically after a rebuild.

---

## 11. Troubleshooting

| Symptom | Likely cause | Resolution |
|---|---|---|
| Connectivity card shows an error | EKCP not running or wrong URL | Start EKCP; verify `NEXT_PUBLIC_EKCP_URL` / Settings API base URL; confirm `GET /health/live` from a terminal. |
| Chat input stays disabled | Missing required settings | Open **Settings** and set Tenant ID, User ID, and API key. |
| `401`/`403` on chat | Missing/invalid API key or tenant mismatch | Re-enter the API key; ensure the tenant in Settings matches the security-context tenant EKCP expects. |
| Tokens arrive all at once, not streamed | Proxy is buffering the SSE response | Disable response buffering for `/chat/stream` at the proxy (see §9). |
| Build fails | Type or lint error | Run `npm run typecheck` and `npm run lint` to see the exact failure. |
| Requests go to an unexpected host | Stale `localStorage` API base URL | Clear the app's `localStorage` (key `ekrag.settings.v1`) or reset the API base URL in Settings. |
| Citations never appear | Retrieval returned no sources | Confirm EKIE has published data and EKCP/EKRE are healthy; not all answers carry citations. |

---

## References

- [../master-architecture.md](../master-architecture.md) — Section 11 (Web UI Layer)
- [../../apps/web-ui/README.md](../../apps/web-ui/README.md)
- [../../.github/instructions/nextjs.instructions.md](../../.github/instructions/nextjs.instructions.md)
- [Web-UI-Help_Guide.md](Web-UI-Help_Guide.md)

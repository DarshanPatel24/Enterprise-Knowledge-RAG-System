# EKCP Deployment Guide

**Audience:** Engineers, DevOps, and platform operators.
**Last updated:** 2026-07-08

> Companion documents: [EKCP-Help_Guide.md](EKCP-Help_Guide.md) (operations & API reference) and [EKCP-handbook.md](EKCP-handbook.md) (architecture). Sprint history: [../sprints/ekcp-sprint-track.md](../sprints/ekcp-sprint-track.md).

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Dependency Topology](#3-dependency-topology)
4. [Python Environment Setup](#4-python-environment-setup)
5. [Configuration Reference (.env)](#5-configuration-reference)
6. [Selecting Backends](#6-selecting-backends)
7. [Starting The Service](#7-starting-the-service)
8. [Smoke Test](#8-smoke-test)
9. [Readiness Verification Checklist](#9-readiness-verification-checklist)
10. [Multi-Tenancy & Governance Hardening](#10-multi-tenancy--governance-hardening)
11. [Production Hardening](#11-production-hardening)
12. [Upgrade & Rollback](#12-upgrade--rollback)
13. [Known Gaps & Roadmap](#13-known-gaps--roadmap)

---

## 1. Overview

EKCP (Enterprise Knowledge Chat Platform) is the conversational orchestration
engine of the EK-RAG platform. It runs **local-first**: the default configuration
is fully offline and dependency-free — a deterministic echo model, in-memory
stores, and no network calls. Real backends (a HuggingFace/Ollama chat model,
Redis, Microsoft SQL Server control plane, and live EKRE knowledge) are
**configuration-selected** behind engine seams and are only loaded when enabled.

This guide covers installing, configuring, running, and hardening EKCP. Container
and cluster orchestration are intentionally out of scope (local-first); §9
validates the code-level readiness a real deployment must satisfy.

---

## 2. Prerequisites

### 2.1 Software Requirements

| Software | Version | Notes |
|---|---|---|
| Python | 3.11+ | Required. |
| Git | Latest | To clone the repository. |

The default offline path needs nothing else.

### 2.2 Optional Software

| Software | When needed |
|---|---|
| Ollama | When `EKCP_MODEL__RUNTIME=langchain` and `EKCP_MODEL__PROVIDER=ollama`. |
| HuggingFace model + torch | When `EKCP_MODEL__RUNTIME=langchain` and `EKCP_MODEL__PROVIDER=huggingface`. |
| Redis | When `EKCP_REDIS__ENABLED=true` (live session/cache backend). |
| Microsoft SQL Server + ODBC Driver 18 | When `EKCP_CONTROL_PLANE__DRIVER=mssql` (conversation control plane). |
| A running EKRE service | When `EKCP_KNOWLEDGE__ENABLED=true` (live enterprise knowledge). |
| Langfuse (self-hosted) | When `EKCP_OBSERVABILITY__LANGFUSE_ENABLED=true`. |
| NVIDIA GPU + CUDA | Accelerates local HuggingFace inference. |

### 2.3 Hardware Minimums

| Component | Offline default | With local HF chat model |
|---|---|---|
| CPU | 2 cores | 8+ cores |
| RAM | 4 GB | 16–32 GB |
| Disk | 2 GB | 20+ GB (model cache) |
| GPU | Not required | NVIDIA GPU recommended |

### 2.4 Network

All services run locally. No outbound internet access is required for the offline
path. Outbound access is only needed for the first-time HuggingFace model
download (cache once, then set `HF_HUB_OFFLINE=1`).

---

## 3. Dependency Topology

```
                 ┌────────────────────────────┐
  Web UI / API ─►│   EKCP  (port 8003)         │
   client        │   conversational engine     │
                 └───────────┬────────────────┘
                             │ (optional, config-selected)
         ┌───────────────────┼─────────────────────┬──────────────┐
         ▼                   ▼                     ▼              ▼
   EKRE (8002)          Redis (6379)        SQL Server        Ollama / HF
   knowledge            session/cache       control plane     chat model
   [KNOWLEDGE__]        [REDIS__]           [CONTROL_PLANE__]  [MODEL__]
```

Every dependency is off by default. EKCP degrades gracefully: if EKRE is enabled
but unavailable, knowledge retrieval trips a circuit breaker and falls back to
local memory without failing the conversation (see Help Guide §13).

---

## 4. Python Environment Setup

From the repository root:

```powershell
# Create and activate a virtual environment (once, at the repo root).
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install EKCP runtime dependencies (offline default path).
.\.venv\Scripts\python.exe -m pip install -r services/ekcp/requirements.txt
.\.venv\Scripts\python.exe -m pip install -r packages/contracts/requirements.txt
```

Install optional backend extras only when you enable the corresponding backend:

```powershell
# Live HuggingFace chat model (runtime=langchain, provider=huggingface).
.\.venv\Scripts\python.exe -m pip install -e "services/ekcp[huggingface]"

# Ollama chat model + LangGraph agent runtime.
.\.venv\Scripts\python.exe -m pip install -e "services/ekcp[orchestration]"

# Redis cache + SQL Server control plane + EKRE HTTP client.
.\.venv\Scripts\python.exe -m pip install -e "services/ekcp[backends]"

# Test + type-check tooling.
.\.venv\Scripts\python.exe -m pip install -e "services/ekcp[dev]"
```

The optional-dependency groups are defined in
[services/ekcp/pyproject.toml](../../services/ekcp/pyproject.toml).

---

## 5. Configuration Reference

Copy the template and edit values as needed:

```powershell
Copy-Item services/ekcp/.env.example services/ekcp/.env
```

All configuration is environment-backed with the `EKCP_` prefix and the nested
`__` delimiter. Nothing is hardcoded — every operational value is a knob. The
`.env` file is resolved relative to `services/ekcp/` regardless of the working
directory. The full template is [services/ekcp/.env.example](../../services/ekcp/.env.example).

### 5.1 Top Level

| Variable | Default | Meaning |
|---|---|---|
| `EKCP_APP_NAME` | `ekcp` | Service name. |
| `EKCP_ENVIRONMENT` | `local` | Environment label. |

### 5.2 API Gateway (`EKCP_GATEWAY__`)

| Variable | Default | Meaning |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address. |
| `PORT` | `8003` | Service port. |
| `CORS_ALLOW_ORIGINS` | *(blank)* | Comma-separated origins; blank disables CORS. |
| `REQUEST_TIMEOUT_SECONDS` | `30.0` | Request timeout. |

### 5.3 Observability (`EKCP_OBSERVABILITY__`)

| Variable | Default | Meaning |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Log level. |
| `SERVICE_NAME` | `ekcp` | Logical service name in logs/traces. |
| `LANGFUSE_ENABLED` | `false` | Enable self-hosted Langfuse tracing. |
| `LANGFUSE_URL` | `http://localhost:3000` | Langfuse endpoint. |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | *(blank)* | Langfuse credentials. |
| `OTEL_EXPORTER_ENDPOINT` | *(unset)* | Optional OpenTelemetry endpoint. |

### 5.4 Security Ingress (`EKCP_SECURITY__`)

| Variable | Default | Meaning |
|---|---|---|
| `REQUIRE_SECURITY_CONTEXT` | `true` | Reject governed requests without a valid security context. |
| `DEFAULT_CLEARANCE` | `public` | Default classification clearance. |
| `REQUIRE_GATEWAY_AUTH` | `false` (code) / `true` (`.env`) | Require the shared gateway token on every governed request. |
| `GATEWAY_AUTH_TOKEN` | *(blank)* | Shared bearer token the trusted upstream must present (a secret; change it). |
| `TRUST_REQUEST_ROLES` | `true` | When false, client-supplied roles are ignored and only `DEFAULT_ROLE` applies. |

> **Gateway authentication.** When `REQUIRE_GATEWAY_AUTH=true`, every governed
> route requires the token via `Authorization: Bearer <token>` or an
> `X-Service-Token` header. Health and readiness probes stay open. If the flag is
> on but `GATEWAY_AUTH_TOKEN` is blank, EKCP fails closed (503) rather than
> allowing unauthenticated access. The token is redacted from logs.

### 5.5 Redis (`EKCP_REDIS__`)

| Variable | Default | Meaning |
|---|---|---|
| `ENABLED` | `false` | Use live Redis instead of in-memory state. |
| `HOST` / `PORT` / `DB` | `localhost` / `6379` / `0` | Connection target. |
| `PASSWORD` | *(blank)* | Redis password (treat as a secret). |
| `REQUEST_TIMEOUT_SECONDS` | `5.0` | Connection timeout. |

### 5.6 Control Plane (`EKCP_CONTROL_PLANE__`)

| Variable | Default | Meaning |
|---|---|---|
| `DRIVER` | `inmemory` | `inmemory` or `mssql`. |
| `URL` | *(blank)* | SQL Server connection URL when `DRIVER=mssql`. |

### 5.7 Conversation (`EKCP_CONVERSATION__`)

| Variable | Default | Meaning |
|---|---|---|
| `DEFAULT_WORKSPACE_ID` | `default` | Workspace when unspecified. |
| `DEFAULT_LANGUAGE` | `en` | Default language. |
| `DEFAULT_PRIORITY` | `normal` | Default priority. |
| `ARCHIVE_ON_COMPLETE` | `false` | Archive conversations on completion. |
| `ENABLE_EVENTS` | `true` | Emit conversation lifecycle events. |
| `EVENT_SINK` | `memory` | `memory` (queryable) or `logging`. |

### 5.8 Session (`EKCP_SESSION__`)

| Variable | Default | Meaning |
|---|---|---|
| `SESSION_TTL_SECONDS` | `3600.0` | Session lifetime. |
| `MAX_CONCURRENT_SESSIONS` | `8` | Concurrent sessions per user. |

### 5.9 Intent (`EKCP_INTENT__`)

| Variable | Default | Meaning |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | `0.6` | Below this, the gate asks for clarification. |
| `DEFAULT_LANGUAGE` | `en` | Default language. |
| `ENABLE_LLM_INTENT` | `false` | Reserved; deterministic classifier by default. |

### 5.10 Context (`EKCP_CONTEXT__`)

| Variable | Default | Meaning |
|---|---|---|
| `MAX_CONTEXT_TOKENS` | `8000` | Context window budget. |
| `CHARS_PER_TOKEN` | `4` | Token estimation heuristic. |
| `MIN_RELEVANCE` | `0.0` | Minimum relevance to retain an item. |
| `DEDUPE_CONTENT` | `true` | Drop duplicate content. |
| `RESERVE_RATIO` | `0.1` | Fraction reserved for generation headroom. |

### 5.11 Prompt (`EKCP_PROMPT__`)

| Variable | Default | Meaning |
|---|---|---|
| `DEFAULT_TEMPLATE_ID` | `enterprise_chat_v1` | Default prompt template. |
| `MAX_PROMPT_TOKENS` | `12000` | Prompt token budget. |
| `CHARS_PER_TOKEN` | `4` | Token estimation heuristic. |
| `ASSISTANT_IDENTITY` | `the enterprise knowledge assistant` | Injected identity (not hardcoded). |
| `ASSISTANT_BEHAVIOR` | `Be accurate, concise, and policy-compliant.` | Injected behavior. |
| `DEFAULT_OUTPUT_FORMAT` | `markdown` | Default output format. |

### 5.12 Model Gateway (`EKCP_MODEL__`)

| Variable | Default | Meaning |
|---|---|---|
| `RUNTIME` | `deterministic` | `deterministic` (offline echo) or `langchain` (real model). |
| `PROVIDER` | `huggingface` | `huggingface` or `ollama` (when `RUNTIME=langchain`). |
| `MODEL_NAME` | *(blank)* | Provider model identifier. |
| `BASE_URL` | `http://localhost:11434` | Provider base URL (e.g., Ollama). |
| `TEMPERATURE` | `0.0` | Sampling temperature. |
| `CONTEXT_WINDOW` | `8192` | Model context window. |
| `MAX_OUTPUT_TOKENS` | `2048` | Max generated tokens. |
| `PROMPT_COST_PER_1K` / `COMPLETION_COST_PER_1K` | `0.0` | Cost accounting rates. |
| `ROUTING_STRATEGY` | `hybrid` | `capability` / `cost` / `latency` / `quality` / `policy` / `hybrid`. |
| `DEFAULT_MODEL_ID` | *(blank)* | Blank auto-selects the active model. |
| `ENABLE_FALLBACK` | `true` | Enable automatic model fallback. |
| `REQUIRE_APPROVED` | `true` | Only route to approved/production models. |
| `MAX_TOKENS_PER_REQUEST` | `0` | Per-request token ceiling (0 = unlimited). |
| `MAX_COST_PER_REQUEST` | `0.0` | Per-request cost ceiling (0 = unlimited). |
| `CHARS_PER_TOKEN` | `4` | Token estimation heuristic. |

### 5.13 Memory (`EKCP_MEMORY__`)

| Variable | Default | Meaning |
|---|---|---|
| `WORKING_TTL_SECONDS` | `1800.0` | Working-memory retention. |
| `SESSION_TTL_SECONDS` | `28800.0` | Session-memory retention. |
| `CONVERSATION_TTL_SECONDS` | `2592000.0` | Conversation-memory retention. |
| `WORKSPACE_TTL_SECONDS` | `31536000.0` | Workspace-memory retention. |
| `USER_TTL_SECONDS` | `94608000.0` | User-memory retention. |
| `ORGANIZATIONAL_TTL_SECONDS` | `0.0` | Organizational retention (0 = indefinite). |
| `DEFAULT_MIN_CONFIDENCE` | `0.5` | Minimum confidence to recall. |
| `DEFAULT_CLASSIFICATION` | `internal` | Default memory classification. |
| `MAX_RETRIEVAL_LIMIT` | `10` | Max memories returned. |
| `WEIGHT_RELEVANCE` / `WEIGHT_RECENCY` / `WEIGHT_IMPORTANCE` / `WEIGHT_FREQUENCY` / `WEIGHT_TRUST` | `0.4` / `0.2` / `0.15` / `0.1` / `0.15` | Ranking weights. |
| `RECENCY_HALF_LIFE_HOURS` | `24.0` | Recency decay half-life. |

### 5.14 Tools (`EKCP_TOOLS__`)

| Variable | Default | Meaning |
|---|---|---|
| `DEFAULT_TIMEOUT_SECONDS` | `10.0` | Tool execution timeout. |
| `MAX_ATTEMPTS` | `2` | Bounded retry attempts. |
| `ENFORCE_PERMISSIONS` | `true` | Require all permissions a tool declares. |

### 5.15 Agent (`EKCP_AGENT__`)

| Variable | Default | Meaning |
|---|---|---|
| `RUNNER` | `sequential` | `sequential` (offline) or `langgraph` (graph + checkpointer). |
| `MAX_STEPS` | `4` | Bounded steps per execution. |
| `BASE_CONFIDENCE` | `0.85` | Baseline outcome confidence. |

### 5.16 Planning (`EKCP_PLANNING__`)

| Variable | Default | Meaning |
|---|---|---|
| `MAX_TASKS` | `12` | Max tasks per plan. |
| `DEFAULT_TASK_TIMEOUT_SECONDS` | `60.0` | Default task timeout. |

### 5.17 Governance (`EKCP_GOVERNANCE__`)

| Variable | Default | Meaning |
|---|---|---|
| `ENFORCE_AUTHORIZATION` | `true` | Enforce RBAC/ABAC on governed operations. |
| `ENABLE_AUDIT` | `true` | Record an audit trail. |
| `AUDIT_SINK` | `memory` | `memory` (queryable, ephemeral) / `logging` / `file` (durable append-only JSONL). |
| `AUDIT_FILE_PATH` | `./storage/audit/ekcp_audit.jsonl` | Path for the `file` sink (append-only, survives restarts). |
| `ENABLE_MASKING` | `true` | Mask PII in outbound responses. |
| `MASK_EMAIL` / `MASK_PHONE` / `MASK_SSN` / `MASK_CREDIT_CARD` | `true` | Per-type masking toggles. |
| `MASK_INBOUND` | `true` | Mask PII in inbound content (e.g. memory writes) before it is persisted. |
| `ALLOW_CLASSIFICATION_DOWNGRADE` | `false` | Block classification downgrades by default. |
| `POLICY_VERSION` | `v1` | Policy version stamped on decisions. |
| `DEFAULT_ROLE` | `power_user` | `admin` / `power_user` / `user` / `service` / `agent`. |

### 5.18 Knowledge / EKRE (`EKCP_KNOWLEDGE__`)

| Variable | Default | Meaning |
|---|---|---|
| `ENABLED` | `false` | Fetch live knowledge from EKRE. |
| `BASE_URL` | `http://localhost:8002` | EKRE service URL. |
| `TIMEOUT_SECONDS` | `10.0` | Retrieval timeout. |
| `MAX_RETRIES` | `3` | Retry budget. |
| `CIRCUIT_BREAKER_THRESHOLD` | `5` | Failures before the breaker opens. |
| `CIRCUIT_BREAKER_RESET_SECONDS` | `60.0` | Half-open probe delay. |
| `RETRIEVAL_MODE` | `hybrid` | `semantic` / `keyword` / `hybrid`. |
| `MAX_CANDIDATES` | `10` | Max candidates requested. |
| `RELEVANCE_THRESHOLD` | `0.5` | Minimum candidate relevance. |

### 5.19 Workflow (`EKCP_WORKFLOW__`)

| Variable | Default | Meaning |
|---|---|---|
| `ENABLE_EVENTS` | `true` | Emit platform events. |
| `EVENT_BUS` | `memory` | `memory` (queryable) or `logging`. |
| `SOURCE_SERVICE` | `ekcp` | Event source label. |

### 5.20 Deployment & Readiness (`EKCP_DEPLOYMENT__`)

| Variable | Default | Meaning |
|---|---|---|
| `REPLICAS` | `2` | Configured replica count (HA readiness). |
| `CIRCUIT_BREAKER_THRESHOLD` | `5` | Resilience threshold. |
| `TENANT_MAX_CONCURRENT` | `8` | Per-tenant concurrent request ceiling (0 = unlimited). |
| `TENANT_AWARE_OBSERVABILITY` | `true` | Require tenant/correlation ids in logs/traces. |
| `FIRST_RESPONSE_LATENCY_BUDGET_MS` | `3000.0` | First-response latency NFR budget. |
| `MIN_AVAILABILITY` | `0.999` | Availability NFR target. |
| `MIN_CONVERSATION_COMPLETION` | `0.99` | Handoff KPI target. |
| `MIN_TOOL_SUCCESS` | `0.99` | Handoff KPI target. |
| `MIN_AGENT_ORCHESTRATION` | `0.99` | Handoff KPI target. |
| `MIN_CONVERSATION_RECOVERY` | `1.0` | Handoff KPI target. |
| `MIN_POLICY_COVERAGE` | `1.0` | Handoff KPI target. |
| `MIN_AUDIT_COVERAGE` | `1.0` | Handoff KPI target. |

---

## 6. Selecting Backends

EKCP runs fully offline by default. Enable each backend independently — no code
change is required, only configuration.

### 6.1 Live Chat Model (HuggingFace or Ollama)

```dotenv
EKCP_MODEL__RUNTIME=langchain
EKCP_MODEL__PROVIDER=ollama          # or huggingface
EKCP_MODEL__MODEL_NAME=llama3.1
EKCP_MODEL__BASE_URL=http://localhost:11434
```

Install the matching extra (`[orchestration]` for Ollama, `[huggingface]` for HF).
When left at `RUNTIME=deterministic`, the gateway uses the dependency-free echo
model and never imports a provider.

### 6.2 Live Enterprise Knowledge (EKRE)

```dotenv
EKCP_KNOWLEDGE__ENABLED=true
EKCP_KNOWLEDGE__BASE_URL=http://localhost:8002
```

Requires the `[backends]` extra (httpx) and a running EKRE service. If EKRE is
unavailable, retrieval degrades gracefully to local memory.

### 6.3 Redis Session/Cache

```dotenv
EKCP_REDIS__ENABLED=true
EKCP_REDIS__HOST=localhost
EKCP_REDIS__PORT=6379
```

### 6.4 SQL Server Control Plane

```dotenv
EKCP_CONTROL_PLANE__DRIVER=mssql
EKCP_CONTROL_PLANE__URL=mssql+pyodbc://<host>/<db>?driver=ODBC+Driver+18+for+SQL+Server
```

### 6.5 LangGraph Agent Runtime

```dotenv
EKCP_AGENT__RUNNER=langgraph
```

Requires the `[orchestration]` extra. The default `sequential` runner is
deterministic and in-process.

---

## 7. Starting The Service

```powershell
.\.venv\Scripts\python.exe services/ekcp/scripts/start_api.py
```

This launches uvicorn on `EKCP_GATEWAY__HOST:PORT` (default `0.0.0.0:8003`) using
the configured log level. Equivalent module form:

```powershell
Push-Location services/ekcp/src
..\..\..\.venv\Scripts\python.exe -m uvicorn api.app:app --host 0.0.0.0 --port 8003
Pop-Location
```

---

## 8. Smoke Test

Confirm liveness and readiness:

```powershell
curl.exe http://localhost:8003/health/live
curl.exe http://localhost:8003/health/ready
```

Both return `{"status": ...,"service":"ekcp"}`. Then exercise the offline chat
stream (every governed request requires the `X-Tenant-ID` header and a matching
security context):

```powershell
curl.exe -N -X POST http://localhost:8003/chat/stream `
  -H "X-Tenant-ID: tenant-a" -H "Content-Type: application/json" `
  -d '{"message":"hello","security_context":{"user_id":"u1","tenant_id":"tenant-a","classification_clearance":"internal"}}'
```

You should see `event: token` frames followed by an `event: done` frame.

> If `EKCP_SECURITY__REQUIRE_GATEWAY_AUTH=true`, add the gateway token to every
> governed request: `-H "Authorization: Bearer <GATEWAY_AUTH_TOKEN>"` (or
> `-H "X-Service-Token: <GATEWAY_AUTH_TOKEN>"`). Health and readiness probes do
> not require it.

---

## 9. Readiness Verification Checklist

EKCP exposes code-level readiness assessments. After configuring a deployment,
verify all three report `ready: true`:

```powershell
curl.exe http://localhost:8003/v1/readiness           # deployment topology
curl.exe http://localhost:8003/v1/readiness/tenancy   # multi-tenant isolation
curl.exe http://localhost:8003/v1/readiness/handoff   # master integration KPIs
```

Checklist:

- [ ] `/v1/readiness` reports `ready: true` (replicas ≥ 2, circuit breaker set, tenant ceiling set, latency and availability within NFR).
- [ ] `/v1/readiness/tenancy` reports `ready: true` (tenant boundary, admission ceiling, tenant-aware observability).
- [ ] `/v1/readiness/handoff` reports `ready: true` and lists the 16 endpoints and 4 contracts with policy/audit coverage at 1.0.
- [ ] `/health/live` and `/health/ready` both return 200.
- [ ] Governance is enforced (`EKCP_GOVERNANCE__ENFORCE_AUTHORIZATION=true`) and audit is enabled.

A `warning` finding does not block readiness (`ready` stays true); an `error`
finding does. Review the `findings` array to interpret each check.

---

## 10. Multi-Tenancy & Governance Hardening

- **Gateway authentication.** Set `EKCP_SECURITY__REQUIRE_GATEWAY_AUTH=true` and a
  strong random `GATEWAY_AUTH_TOKEN` so only the trusted upstream gateway can reach
  EKCP. EKCP performs no user authentication of its own — it trusts the gateway to
  authenticate the end user and set identity, roles, and clearance. Enforce that
  boundary (this token, plus mTLS/network policy) before any exposure beyond a
  trusted local network.
- **Least-privilege roles.** Keep `EKCP_GOVERNANCE__DEFAULT_ROLE=user` and leave
  `EKCP_SECURITY__TRUST_REQUEST_ROLES=true` only when the gateway derives roles
  from a verified token. Set it to `false` to ignore request-body roles entirely
  and pin every caller to the default role, preventing self-elevation.
- **Tenant isolation & admission control.** Every request is scoped by
  `X-Tenant-ID` and filtered by `tenant_id`. `EKCP_DEPLOYMENT__TENANT_MAX_CONCURRENT`
  is enforced at request time — a tenant exceeding its ceiling receives `429`; `0`
  disables admission control (flagged as a warning at readiness).
- **Input bounds.** User-supplied text is length-bounded at ingress (messages,
  intents, tasks, objectives, and memory content at 16000 chars; assembled prompts
  at 200000) to bound token cost and resource use.
- **Security context.** Keep `EKCP_SECURITY__REQUIRE_SECURITY_CONTEXT=true` so no
  governed request executes without a validated security context.
- **Authorization.** Keep `EKCP_GOVERNANCE__ENFORCE_AUTHORIZATION=true`.
- **Audit.** Use `AUDIT_SINK=memory` in dev to query `/governance/audit`; use
  `file` (durable append-only JSONL at `AUDIT_FILE_PATH`, survives restarts) for
  production compliance evidence, or `logging` to stream into your log pipeline.
- **PII masking.** Keep `ENABLE_MASKING=true`; outbound model and agent responses
  are masked before they leave the service. Keep `MASK_INBOUND=true` to also scrub
  PII from inbound content (memory writes) before it is persisted.
- **Classification.** Keep `ALLOW_CLASSIFICATION_DOWNGRADE=false` so security
  context propagated to EKRE never downgrades classification.

---

## 11. Production Hardening

- **Secrets.** Never commit `.env`. Provide `EKCP_REDIS__PASSWORD`,
  `EKCP_CONTROL_PLANE__URL`, and `EKCP_OBSERVABILITY__LANGFUSE_SECRET_KEY` via a
  secret manager or environment injection. Secret log redaction is installed
  automatically at startup.
- **CORS.** Set `EKCP_GATEWAY__CORS_ALLOW_ORIGINS` to the explicit Web UI origin;
  leave blank to disable cross-origin entirely.
- **Tracing.** Enable self-hosted Langfuse (`LANGFUSE_ENABLED=true`) and provide
  keys to capture end-to-end traces. Do not point at any external/cloud host.
- **High availability.** Run `REPLICAS ≥ 2` behind a load balancer; EKCP is
  stateless on the offline path and externalizes state to Redis/SQL Server when
  those backends are enabled.
- **Resilience.** Tune `EKCP_KNOWLEDGE__CIRCUIT_BREAKER_THRESHOLD` /
  `_RESET_SECONDS` and `EKCP_MODEL__ENABLE_FALLBACK` for your dependency SLAs.
- **Model caching.** Pre-download HuggingFace models, then set `HF_HUB_OFFLINE=1`
  to prevent runtime network calls.

---

## 12. Upgrade & Rollback

1. Pull the new revision and re-run the green gate:

   ```powershell
   .\.venv\Scripts\python.exe -m ruff check services/ekcp
   Push-Location services/ekcp; ..\..\.venv\Scripts\python.exe -m mypy src; Pop-Location
   Push-Location services/ekcp; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location
   ```

2. Reconcile `.env` against `.env.example` for any new configuration keys.
3. Restart the service and re-run the §9 readiness checklist.
4. **Rollback:** revert to the previous revision and restart. The offline path
   holds no persistent state; with Redis/SQL Server enabled, follow your standard
   backend restore procedure.

---

## 13. Known Gaps & Roadmap

- **Container/cluster orchestration is out of scope.** EKCP is local-first; the
  readiness endpoints validate the *configuration* a real deployment must satisfy
  rather than provisioning infrastructure.
- **Live backend adapters** (SQL Server control plane, Redis session store) are
  config-selected seams; the default persistence is in-memory.
- Track status and acceptance evidence in
  [../sprints/ekcp-sprint-track.md](../sprints/ekcp-sprint-track.md).

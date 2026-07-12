# EKRE Deployment Guide

**Audience:** Engineers, DevOps, and platform operators.
**Last updated:** 2026-07-11

> Companion documents: [EKRE-Help_Guide.md](EKRE-Help_Guide.md) (operations & API reference) and [EKRE-handbook.md](EKRE-handbook.md) (architecture). Sprint history: [../sprints/ekre-sprint-track.md](../sprints/ekre-sprint-track.md).

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
10. [Security & Governance Hardening](#10-security--governance-hardening)
11. [Production Hardening](#11-production-hardening)
12. [Upgrade & Rollback](#12-upgrade--rollback)
13. [Known Gaps & Roadmap](#13-known-gaps--roadmap)

---

## 1. Overview

EKRE (Enterprise Knowledge Retrieval Engine) is the retrieval engine of the
EK-RAG platform. It turns a user query into a ranked, citation-preserving,
policy-compliant `RetrievalContextPackage` and hands it to EKCP for response
generation. EKRE never ingests or embeds documents and never generates
responses — it reads the vectors EKIE published, **inheriting the embedding
model, dimension, and distance metric** from the target collection.

EKRE runs **local-first**: the default configuration is fully offline and
dependency-free — an in-memory connector and a deterministic hash query embedder,
with no network calls. Real backends (a shared Qdrant vector database, a live
HuggingFace/Ollama query-embedding model, and a cross-encoder reranker) are
**configuration-selected** behind engine seams and are only loaded when enabled.

This guide covers installing, configuring, running, and hardening EKRE. Container
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
| Qdrant (self-hosted) | When `EKRE_WORKERS__CONNECTOR=qdrant` (live vector retrieval). Must be the same instance EKIE published to. |
| HuggingFace model + torch | When `EKRE_WORKERS__QUERY_EMBEDDER=langchain` and `EKRE_EMBEDDING__PROVIDER=huggingface`. |
| Ollama | When `EKRE_EMBEDDING__PROVIDER=ollama` (loads the inherited model through Ollama). |
| Cross-encoder reranker model | When `EKRE_RANKING__ENABLE_RERANKER=true` (e.g. `BAAI/bge-reranker-base`; needs the `huggingface` extra). |
| A running EKIE ingestion path | Required to populate the Qdrant collection EKRE reads. |
| Langfuse (self-hosted) | When `EKRE_OBSERVABILITY__LANGFUSE_ENABLED=true`. |
| NVIDIA GPU + CUDA | Accelerates local HuggingFace embedding/reranker inference. |

### 2.3 Hardware Minimums

| Component | Offline default | With live Qdrant + HF query model |
|---|---|---|
| CPU | 2 cores | 8+ cores |
| RAM | 4 GB | 16 GB |
| Disk | 2 GB | 10+ GB (model cache) |
| GPU | Not required | Optional (embedding/reranker run well on CPU) |

> The reference deployment runs the query embedder and reranker on **CPU**
> (`EKRE_EMBEDDING__DEVICE=cpu`, `EKRE_RANKING__RERANKER_DEVICE=cpu`) so the EKCP
> chat LLM keeps the GPU. `BAAI/bge-base-en-v1.5` and `BAAI/bge-reranker-base` are
> both small and fast on CPU.

### 2.4 Network

All services run locally. No outbound internet access is required for the offline
path. Outbound access is only needed for the first-time HuggingFace model
download (cache once, then set `HF_HUB_OFFLINE=1`).

---

## 3. Dependency Topology

```
                 ┌────────────────────────────┐
   EKCP (8003) ─►│   EKRE  (port 8002)         │
   knowledge     │   retrieval engine          │
   client        └───────────┬────────────────┘
                             │ (config-selected)
         ┌───────────────────┼─────────────────────┐
         ▼                   ▼                     ▼
   Qdrant (6333)       HF / Ollama          Langfuse (3000)
   vector DB           query embedder        tracing (optional)
   [WORKERS__/QDRANT__] [EMBEDDING__]         [OBSERVABILITY__]
```

EKRE reads the **same** Qdrant collection EKIE wrote, and inherits that
collection's embedding model, dimension, and distance metric at runtime (the
"sameness rule"). On the offline default path none of these dependencies are
contacted — retrieval runs entirely in-memory.

---

## 4. Python Environment Setup

From the repository root:

```powershell
# Create and activate a virtual environment (once, at the repo root).
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install EKRE runtime dependencies (offline default path).
.\.venv\Scripts\python.exe -m pip install -r services/ekre/requirements.txt
.\.venv\Scripts\python.exe -m pip install -r packages/contracts/requirements.txt
```

Install optional backend extras only when you enable the corresponding backend:

```powershell
# Live HuggingFace query embedding + cross-encoder reranker.
.\.venv\Scripts\python.exe -m pip install -e "services/ekre[huggingface]"

# Live retrieval path (Qdrant client + Ollama runtime).
.\.venv\Scripts\python.exe -m pip install -e "services/ekre[retrieval]"

# Test + type-check tooling.
.\.venv\Scripts\python.exe -m pip install -e "services/ekre[dev]"
```

The optional-dependency groups are defined in
[services/ekre/pyproject.toml](../../services/ekre/pyproject.toml). For an NVIDIA
GPU, install a CUDA build of `torch` matching your driver instead of the default
CPU wheel.

---

## 5. Configuration Reference

Copy the template and edit values as needed:

```powershell
Copy-Item services/ekre/.env.example services/ekre/.env
```

All configuration is environment-backed with the `EKRE_` prefix and the nested
`__` delimiter. Nothing is hardcoded — every operational value is a knob. The
`.env` file is resolved relative to `services/ekre/` regardless of the working
directory. The full template is [services/ekre/.env.example](../../services/ekre/.env.example).

> **Inheritance (sameness rule).** The embedding model, dimension, and distance
> metric are read from the live Qdrant collection at runtime. The
> `EKRE_EMBEDDING__FALLBACK_MODEL`, `EKRE_INHERITANCE__FALLBACK_*` values are
> documented fallbacks only, used when a value cannot be resolved and
> `ALLOW_CONFIG_FALLBACK=true`.

### 5.1 Top Level

| Variable | Default | Meaning |
|---|---|---|
| `EKRE_APP_NAME` | `ekre` | Service name. |
| `EKRE_ENVIRONMENT` | `local` | Environment label. |

### 5.2 API Gateway (`EKRE_GATEWAY__`)

| Variable | Default | Meaning |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address (`127.0.0.1` restricts to localhost). |
| `PORT` | `8002` | Service port. |

### 5.3 Qdrant Vector Database (`EKRE_QDRANT__`)

| Variable | Default | Meaning |
|---|---|---|
| `HOST` / `PORT` | `localhost` / `6333` | Qdrant connection (shared with EKIE). |
| `URL` / `API_KEY` | *(blank)* | Optional full URL + key; when blank, host/port are used. |
| `REQUEST_TIMEOUT_SECONDS` | `30.0` | Client timeout. |
| `PAYLOAD_METADATA_KEY` | `metadata` | Key under which EKIE nests governance metadata; `""` for top-level fields. |

### 5.4 Observability (`EKRE_OBSERVABILITY__`)

| Variable | Default | Meaning |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Log level. |
| `SERVICE_NAME` | `ekre` | Logical service name in logs/traces. |
| `LANGFUSE_ENABLED` | `false` | Enable self-hosted Langfuse tracing. |
| `LANGFUSE_URL` | `http://localhost:3000` | Langfuse endpoint. |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | *(blank)* | Langfuse credentials (secret). |

### 5.5 Retrieval Behavior (`EKRE_RETRIEVAL__`)

| Variable | Default | Meaning |
|---|---|---|
| `DEFAULT_COLLECTION` | `enterprise_documents` | Collection EKIE published into (source of the inherited profile). |
| `ALLOWED_COLLECTIONS` | *(blank)* | Comma-separated client allowlist; blank permits only the default collection for overrides. |
| `SEARCH_TYPE` | `similarity` | Retriever search type. |
| `DEFAULT_TOP_K` | `5` | Default candidate count. |
| `BUDGET_*_MS` | see `.env.example` | SLO latency targets for the stage-timeline report only; they do **not** cap execution. |

### 5.6 Query Embedding Runtime (`EKRE_EMBEDDING__`)

| Variable | Default | Meaning |
|---|---|---|
| `PROVIDER` | `huggingface` | How the query is embedded (`huggingface` or `ollama`); must load the same model EKIE used. |
| `FALLBACK_MODEL` | *(blank)* | Fallback model id if the inherited model cannot be resolved. |
| `BASE_URL` | `http://localhost:11434` | Ollama base URL (ignored by HuggingFace). |
| `DEVICE` | `auto` | `auto` / `cpu` / `cuda` for the HuggingFace provider. |
| `TORCH_DTYPE` | `auto` | Precision for the HuggingFace provider. |
| `NORMALIZE_VECTORS` | `true` | L2-normalize query vectors. |

### 5.7 Inheritance (`EKRE_INHERITANCE__`)

| Variable | Default | Meaning |
|---|---|---|
| `ALLOW_CONFIG_FALLBACK` | `true` | When false, unresolved inherited values raise instead of using fallbacks. |
| `FALLBACK_EMBEDDING_MODEL` | *(blank)* | Fallback embedding model id. |
| `FALLBACK_DIMENSION` | `0` | Fallback vector dimension. |
| `FALLBACK_DISTANCE_METRIC` | `cosine` | Fallback distance metric. |

### 5.8 Security Ingress (`EKRE_SECURITY__`)

| Variable | Default | Meaning |
|---|---|---|
| `REQUIRE_SECURITY_CONTEXT` | `true` | Reject retrieval requests without a valid security context. |
| `REQUIRE_TENANT_SCOPE` | `true` | Scope retrieval to the requesting tenant at the DB boundary and re-check in-process. |
| `DEFAULT_CLEARANCE` | `public` | Default classification clearance. |
| `REQUIRE_SIGNED_CONTEXT` | `false` | Require a signed JWT security context in `X-Security-Context` instead of a self-asserted body. |
| `CONTEXT_SIGNING_SECRET` | *(blank)* | Shared HMAC secret (a secret; shared with EKCP). |
| `CONTEXT_SIGNING_ALGORITHM` | `HS256` | `HS256` / `HS384` / `HS512`. |
| `CONTEXT_ISSUER` / `CONTEXT_AUDIENCE` | *(blank)* | Checked when set. |
| `CONTEXT_LEEWAY_SECONDS` | `30` | Clock-skew leeway for `exp`/`nbf`/`iat`. |

### 5.9 Query Intelligence (`EKRE_QUERY__`)

| Variable | Default | Meaning |
|---|---|---|
| `MAX_QUERY_LENGTH` | `2048` | Reject longer queries. |
| `DEFAULT_LANGUAGE` | `en` | Default language. |
| `CANDIDATE_COUNT_*` | 5 / 50 / 20 / 30 / 10 | Candidate counts per profile (precision/recall/balanced/compliance/performance). |
| `ENABLE_LLM_INTERPRETER` | `false` | Optional LangChain query interpreter; deterministic rules are the default and fallback. |
| `LLM_PROVIDER` / `LLM_MODEL` / `LLM_BASE_URL` | `huggingface` / *(blank)* / `:11434` | Interpreter model config (dynamic provider). |

### 5.10 Execution Core (`EKRE_EXECUTION__`)

| Variable | Default | Meaning |
|---|---|---|
| `RUNNER` | `concurrent` | `concurrent` (deterministic default) or `langgraph`. |
| `MAX_PARALLEL_WORKERS` | `4` | Thread-pool size for parallel workers. |
| `DEFAULT_TASK_TIMEOUT_MS` | `30000.0` | Hard per-task kill-timeout (wall clock for one live worker call). Keep above real embedding latency. |
| `MAX_ATTEMPTS_PER_TASK` | `1` | Per-task retry attempts. |
| `ADMISSION_ENABLED` | `true` | Reject empty-tenant / non-positive-limit tasks. |
| `FAIL_OPEN` | `true` | Return an empty result instead of raising when all workers fail. |

### 5.11 Workers & Connector (`EKRE_WORKERS__`)

| Variable | Default | Meaning |
|---|---|---|
| `CONNECTOR` | `inmemory` | `inmemory` (offline default) or `qdrant` (live). |
| `QUERY_EMBEDDER` | `local_hash` | `local_hash` (deterministic offline) or `langchain` (inherited EKIE model). |
| `LOCAL_EMBEDDING_DIMENSION` | `256` | Dimension for the local hash embedder (offline path only). |

### 5.12 Fusion (`EKRE_FUSION__`)

| Variable | Default | Meaning |
|---|---|---|
| `IDENTITY_POLICY` | `chunk` | `chunk` / `document` / `strict` grouping for Reciprocal Rank Fusion. |
| `RRF_K` | `60` | RRF constant (higher = flatter rank weighting). |

### 5.13 Ranking & Reranker (`EKRE_RANKING__`)

| Variable | Default | Meaning |
|---|---|---|
| `CANDIDATE_LIMIT` | `10` | Max ranked objects returned. |
| `MIN_COMPOSITE_SCORE` | `0.0` | Drop objects below this composite score. |
| `SEMANTIC_WEIGHT` / `LEXICAL_WEIGHT` / `METADATA_WEIGHT` / `FUSION_WEIGHT` | 0.4 / 0.2 / 0.1 / 0.3 | Evidence factor weights. |
| `POLICY_VERSION` | `v1` | Versions the weighting policy. |
| `ENABLE_RERANKER` | `false` | Enable the cross-encoder reranker. |
| `RERANKER_MODEL` | *(blank)* | Reranker model id, e.g. `BAAI/bge-reranker-base`. |
| `RERANKER_DEVICE` | `auto` | `auto` / `cpu` / `cuda`. |
| `RERANKER_TORCH_DTYPE` | `auto` | Reranker precision. |
| `RERANKER_TRUST_REMOTE_CODE` | `false` | Allow custom modeling code shipped with the model (enable only for trusted models). |

### 5.14 Context Assembly (`EKRE_ASSEMBLY__`)

| Variable | Default | Meaning |
|---|---|---|
| `MAX_CONTEXT_TOKENS` | `4000` | Token budget for the handoff package. |
| `MAX_OBJECTS` | `10` | Max objects in the package. |
| `ORDERING` | `rank` | `rank` (relevance) or `document` (grouped). |
| `NORMALIZE_WHITESPACE` | `true` | Collapse whitespace in selected content. |
| `DEDUPE_CONTENT` | `true` | Drop duplicate content. |
| `CHARS_PER_TOKEN` | `4` | Char-based token estimate. |
| `MIN_RELEVANCE` | `0.0` | Drop objects below this relevance. |

### 5.15 Governance (`EKRE_GOVERNANCE__`)

| Variable | Default | Meaning |
|---|---|---|
| `ENABLE_AUDIT` | `true` | Emit immutable audit records. |
| `AUDIT_SINK` | `logging` | `logging` (structured logs) or `memory` (in-process, tests). |
| `ENABLE_MASKING` | `true` | Mask PII in the handoff package so no sensitive content reaches EKCP. |
| `MASK_EMAIL` / `MASK_PHONE` / `MASK_SSN` / `MASK_CREDIT_CARD` | `true` | PII categories to mask. |
| `TOTAL_LATENCY_BUDGET_MS` | `500.0` | Budget for the trace over-budget check. |
| `POLICY_VERSION` | `v1` | Governance policy version. |

### 5.16 Deployment & Readiness (`EKRE_DEPLOYMENT__`)

| Variable | Default | Meaning |
|---|---|---|
| `VECTOR_POOL_SIZE` / `KEYWORD_POOL_SIZE` / `METADATA_POOL_SIZE` | 4 / 2 / 2 | Capability-grouped worker pool sizes. |
| `REPLICAS` | `2` | Expected replicas (readiness warns below 2). |
| `CIRCUIT_BREAKER_THRESHOLD` / `_RESET_SECONDS` | `5` / `30.0` | Circuit breaker tuning. |
| `TENANT_MAX_CONCURRENT` | `8` | Max concurrent retrievals per tenant (`0` = unlimited, warns at readiness). |
| `MAX_LATENCY_MS` | `500.0` | NFR latency target. |
| `MIN_AVAILABILITY` | `0.999` | NFR availability target. |
| `EVAL_K` / `MIN_PRECISION_AT_K` / `MIN_RECALL_AT_K` / `MIN_MRR` / `MIN_NDCG` | 10 / 0.5 / 0.5 / 0.5 / 0.5 | Retrieval-quality thresholds. |

---

## 6. Selecting Backends

EKRE runs fully offline by default. Enable each backend independently — no code
change is required, only configuration.

### 6.1 Live Vector Retrieval (Qdrant + inherited model)

```dotenv
EKRE_WORKERS__CONNECTOR=qdrant
EKRE_WORKERS__QUERY_EMBEDDER=langchain
EKRE_EMBEDDING__PROVIDER=huggingface
EKRE_EMBEDDING__DEVICE=cpu
EKRE_QDRANT__HOST=localhost
EKRE_QDRANT__PORT=6333
EKRE_RETRIEVAL__DEFAULT_COLLECTION=enterprise_documents
```

Requires the `[huggingface]` and `[retrieval]` extras and a Qdrant instance
already populated by EKIE. The embedding model, dimension, and distance metric
are inherited from the collection (do not hardcode them). For a fully offline,
no-data smoke test keep `CONNECTOR=inmemory` and `QUERY_EMBEDDER=local_hash`.

### 6.2 Cross-Encoder Reranker

```dotenv
EKRE_RANKING__ENABLE_RERANKER=true
EKRE_RANKING__RERANKER_MODEL=BAAI/bge-reranker-base
EKRE_RANKING__RERANKER_DEVICE=cpu
```

Requires the `[huggingface]` extra (sentence-transformers). The reranker only
reorders candidates (no chat generation — that is EKCP) and degrades gracefully
to the deterministic composite order if the model is unavailable.

### 6.3 Signed Security Context (verifiable trust boundary)

```dotenv
EKRE_SECURITY__REQUIRE_SIGNED_CONTEXT=true
EKRE_SECURITY__CONTEXT_SIGNING_SECRET=<shared-with-EKCP>
EKRE_SECURITY__CONTEXT_SIGNING_ALGORITHM=HS256
```

When enabled, callers must present a signed JWT in the `X-Security-Context`
header; the self-asserted request body is ignored. Enable this only once EKCP is
minting signed contexts with the same shared secret.

### 6.4 LangGraph Execution Runner

```dotenv
EKRE_EXECUTION__RUNNER=langgraph
```

Requires the `[retrieval]` extra. The default `concurrent` runner is
deterministic and thread-pool based.

### 6.5 Langfuse Tracing

```dotenv
EKRE_OBSERVABILITY__LANGFUSE_ENABLED=true
EKRE_OBSERVABILITY__LANGFUSE_URL=http://localhost:3000
EKRE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY=<pk>
EKRE_OBSERVABILITY__LANGFUSE_SECRET_KEY=<sk>
```

---

## 7. Starting The Service

```powershell
.\.venv\Scripts\python.exe services/ekre/scripts/start_api.py
```

This launches uvicorn on `EKRE_GATEWAY__HOST:PORT` (default `0.0.0.0:8002`) using
the configured log level. Equivalent module form:

```powershell
Push-Location services/ekre/src
..\..\..\.venv\Scripts\python.exe -m uvicorn api.app:app --host 0.0.0.0 --port 8002
Pop-Location
```

---

## 8. Smoke Test

Confirm liveness and readiness:

```powershell
curl.exe http://localhost:8002/health/live
curl.exe http://localhost:8002/health/ready
```

Inspect the resolved (inherited or fallback) retrieval profile — this proves no
model/metric is hardcoded:

```powershell
curl.exe http://localhost:8002/v1/retrieval/config -H "X-Tenant-ID: tenant-a"
```

Run a retrieval (every request requires the `X-Tenant-ID` header and a matching
security context):

```powershell
curl.exe -X POST http://localhost:8002/v1/query/retrieve `
  -H "X-Tenant-ID: tenant-a" -H "Content-Type: application/json" `
  -d '{"query":"remote work policy","security_context":{"user_id":"u1","tenant_id":"tenant-a","classification_clearance":"internal"}}'
```

On the offline default path this returns a `TracedRetrieval` with an empty
candidate set and a full stage timeline (no data indexed). With the live Qdrant
connector against an EKIE-populated collection it returns ranked, cited
candidates.

> If `EKRE_SECURITY__REQUIRE_SIGNED_CONTEXT=true`, send the signed JWT via
> `-H "X-Security-Context: <jwt>"` instead of relying on the body context.

---

## 9. Readiness Verification Checklist

EKRE exposes a code-level deployment readiness assessment. After configuring a
deployment, verify it reports `ready: true`:

```powershell
curl.exe http://localhost:8002/v1/readiness
```

Checklist:

- [ ] `/v1/readiness` reports `ready: true` (worker pools ≥ 1, replicas ≥ 2, circuit breaker set, tenant ceiling set, latency and availability within NFR).
- [ ] `/v1/retrieval/config` resolves a profile and reports the embedding model/dimension/distance metric and `source` (`inherited` / `hybrid` / `fallback`).
- [ ] `/health/live` and `/health/ready` both return 200.
- [ ] Security context is required (`REQUIRE_SECURITY_CONTEXT=true`) and tenant scoping is enabled (`REQUIRE_TENANT_SCOPE=true`).
- [ ] Audit and PII masking are enabled.

A `warning` finding does not block readiness (`ready` stays true); an `error`
finding does. Review the `findings` array to interpret each check.

---

## 10. Security & Governance Hardening

- **Tenant isolation.** Keep `EKRE_SECURITY__REQUIRE_TENANT_SCOPE=true`. Retrieval
  is scoped to the requesting tenant at the Qdrant boundary (nested
  `metadata.tenant_id`) and re-checked in-process (defense in depth).
- **Clearance filtering before relevance.** Candidates are filtered by
  `classification_clearance` at the database boundary *before* fusion and ranking.
  Keep `REQUIRE_SECURITY_CONTEXT=true` so no request runs unscoped.
- **Verifiable trust boundary.** For any exposure beyond a trusted local network,
  enable `REQUIRE_SIGNED_CONTEXT=true` with a strong shared secret so EKRE derives
  trust from a signed JWT rather than a self-asserted body. `alg=none` is rejected.
- **Collection scoping.** Use `EKRE_RETRIEVAL__ALLOWED_COLLECTIONS` to restrict
  which collections a client may target; an empty allowlist permits only the
  default collection for overrides.
- **PII masking.** Keep `ENABLE_MASKING=true`; the handoff package is masked so no
  raw PII reaches EKCP. Citations are never altered.
- **Audit.** Use `AUDIT_SINK=memory` in dev for inspection; use `logging` to
  stream immutable audit records into your log pipeline in production.
- **Per-tenant admission.** `EKRE_DEPLOYMENT__TENANT_MAX_CONCURRENT` throttles
  concurrent retrievals per tenant (`429` when exceeded); `0` disables it
  (flagged as a warning at readiness).

---

## 11. Production Hardening

- **Secrets.** Never commit `.env`. Provide `EKRE_QDRANT__API_KEY`,
  `EKRE_SECURITY__CONTEXT_SIGNING_SECRET`, and
  `EKRE_OBSERVABILITY__LANGFUSE_SECRET_KEY` via a secret manager or environment
  injection. Secret values are typed as `SecretStr` and redacted from logs.
- **Bind address.** Set `EKRE_GATEWAY__HOST=127.0.0.1` unless a load balancer or
  gateway fronts EKRE; EKRE is an internal service (its only client is EKCP).
- **Tracing.** Enable self-hosted Langfuse and provide keys to capture the
  end-to-end retrieval trace. Do not point at any external/cloud host.
- **High availability.** Run `REPLICAS ≥ 2` behind a load balancer; EKRE is
  stateless (all state lives in Qdrant, owned by EKIE).
- **Resilience.** Tune `CIRCUIT_BREAKER_THRESHOLD` / `_RESET_SECONDS` and
  `DEFAULT_TASK_TIMEOUT_MS` for your embedding/vector-store latency. Keep the
  task timeout above real embedding latency so completed results are not discarded.
- **Model caching.** Pre-download the HuggingFace embedding/reranker models, then
  set `HF_HUB_OFFLINE=1` to prevent runtime network calls.

---

## 12. Upgrade & Rollback

1. Pull the new revision and re-run the green gate:

   ```powershell
   .\.venv\Scripts\python.exe -m ruff check services/ekre
   Push-Location services/ekre; ..\..\.venv\Scripts\python.exe -m mypy src; Pop-Location
   Push-Location services/ekre; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location
   ```

2. Reconcile `.env` against `.env.example` for any new configuration keys.
3. Restart the service and re-run the §9 readiness checklist.
4. **Rollback:** revert to the previous revision and restart. EKRE holds no
   persistent state of its own; the vector data in Qdrant is owned and versioned
   by EKIE.

> **Vector schema changes.** If EKIE changes the embedding model, dimension, or
> distance metric, EKRE inherits the new profile from the collection
> automatically — but the collection must be re-ingested by EKIE first (a payload
> or schema change requires a clean re-ingest, not just a restart).

---

## 13. Known Gaps & Roadmap

- **Container/cluster orchestration is out of scope.** EKRE is local-first; the
  readiness endpoint validates the *configuration* a real deployment must satisfy
  rather than provisioning infrastructure.
- **Live vector retrieval requires an EKIE-populated Qdrant collection.** With the
  default in-memory connector, `/v1/query/*` returns empty result sets until data
  is indexed.
- Track status and acceptance evidence in
  [../sprints/ekre-sprint-track.md](../sprints/ekre-sprint-track.md).

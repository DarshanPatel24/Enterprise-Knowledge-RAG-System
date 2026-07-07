# EKRE Deployment Guide

> Enterprise Knowledge Retrieval Engine (EKRE) — operational setup, configuration, and production hardening.
> Companion documents: [EKRE-Help_Guide.md](EKRE-Help_Guide.md) (complete reference) and [EKRE-handbook.md](EKRE-handbook.md) (architecture).

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Local-First Infrastructure](#2-local-first-infrastructure)
3. [Python Environment Setup](#3-python-environment-setup)
4. [Configuration Reference](#4-configuration-reference)
5. [Inheritance From EKIE](#5-inheritance-from-ekie)
6. [Starting The Service](#6-starting-the-service)
7. [Verification Checklist](#7-verification-checklist)
8. [Production Hardening](#8-production-hardening)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

EKRE is a stateless retrieval engine. It reads the vectors and metadata that EKIE
published; it never ingests, embeds documents, or generates responses.

| Requirement | Detail |
| --- | --- |
| Python | 3.11+ (repository venv at `.venv`) |
| EKIE published data | For real retrieval, EKIE must have already published vectors to the shared Qdrant collection. Without it, EKRE runs local-first and returns valid, empty results. |
| Shared contracts | `packages/contracts` (installed on the Python path). |
| Optional — live vector store | Qdrant (self-hosted, shared with EKIE) for the production retrieval path. |
| Optional — model runtime | Ollama or a local HuggingFace model to embed the query with the **same** model EKIE used. |

Local-first default: with no external services, EKRE uses an in-memory connector
and a deterministic hash embedder, so the full pipeline and every endpoint work
offline for development and testing.

---

## 2. Local-First Infrastructure

EKRE has **no mandatory infrastructure**. The defaults (`EKRE_WORKERS__CONNECTOR=inmemory`,
`EKRE_WORKERS__QUERY_EMBEDDER=local_hash`) require nothing external.

For the live retrieval path, EKRE connects to the **same Qdrant collection EKIE
published to** — it does not run its own vector database. Reuse the EKIE local
stack (`docker-compose.local.yml` at the repository root brings up Qdrant); EKRE
only needs network access to it.

```powershell
# Confirm Qdrant (shared with EKIE) is reachable, if using the live path:
curl http://localhost:6333/readyz
```

Deployment topology is intentionally separate from the deterministic retrieval
logic; no deployment model changes retrieval behavior.

---

## 3. Python Environment Setup

```powershell
# From the repository root, with the venv active.

# Core service only (local-first / offline path — no external clients):
pip install -e services/ekre

# Live retrieval path (Ollama runtime + Qdrant vector store client):
pip install -e "services/ekre[retrieval]"

# HuggingFace query embedding (to match an EKIE HuggingFace/Qwen model):
pip install -e "services/ekre[huggingface]"

# Development (pytest, mypy, httpx):
pip install -e "services/ekre[dev]"
```

GPU acceleration (NVIDIA): the default `torch` is CPU-only. Install a CUDA build
matching your driver instead, then set `EKRE_EMBEDDING__DEVICE=auto` and
`EKRE_EMBEDDING__TORCH_DTYPE=float16` in `services/ekre/.env`.

Copy the configuration template:

```powershell
Copy-Item services/ekre/.env.example services/ekre/.env
```

---

## 4. Configuration Reference

All values are environment-backed with the `EKRE_` prefix and nested `__`
delimiter, loaded from `services/ekre/.env`. Nothing is hardcoded; the embedding
model, dimension, and distance metric are inherited from EKIE at runtime.

### Application
| Variable | Default | Purpose |
| --- | --- | --- |
| `EKRE_APP_NAME` | `ekre` | Service name. |
| `EKRE_ENVIRONMENT` | `local` | Deployment environment label. |

### Qdrant — `EKRE_QDRANT__` (shared with EKIE)
| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `localhost` | Qdrant host. |
| `PORT` | `6333` | Qdrant port. |
| `URL` | *(blank)* | Full URL; when set, overrides host/port. |
| `API_KEY` | *(blank)* | Qdrant API key (optional). |
| `REQUEST_TIMEOUT_SECONDS` | `30.0` | Client timeout. |

### Observability — `EKRE_OBSERVABILITY__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `LOG_LEVEL` | `INFO` | Root log level. |
| `SERVICE_NAME` | `ekre` | Log/trace service tag. |
| `LANGFUSE_ENABLED` | `false` | Enable Langfuse tracing. |
| `LANGFUSE_HOST` | `http://localhost:3000` | Self-hosted Langfuse host. |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | *(blank)* | Langfuse credentials. |
| `OTEL_EXPORTER_ENDPOINT` | *(unset)* | Optional OpenTelemetry endpoint. |

### Retrieval — `EKRE_RETRIEVAL__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `DEFAULT_COLLECTION` | `enterprise_documents` | Collection EKIE published to. |
| `SEARCH_TYPE` | `similarity` | Retriever search type. |
| `DEFAULT_TOP_K` | `5` | Default candidate count. |
| `BUDGET_QUERY_UNDERSTANDING_MS` | `20.0` | Stage latency budget. |
| `BUDGET_VECTOR_MS` | `150.0` | Stage latency budget. |
| `BUDGET_RANKING_MS` | `100.0` | Stage latency budget. |
| `BUDGET_ASSEMBLY_MS` | `50.0` | Stage latency budget. |
| `BUDGET_TOTAL_MS` | `500.0` | End-to-end latency target. |

### Query embedding runtime — `EKRE_EMBEDDING__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `PROVIDER` | `huggingface` | How the query is embedded (`huggingface` or `ollama`); must load the **same** model EKIE used. |
| `FALLBACK_MODEL` | *(blank)* | Fallback only; the model is inherited from the collection. |
| `BASE_URL` | `http://localhost:11434` | Ollama runtime URL. |
| `REQUEST_TIMEOUT_SECONDS` | `60.0` | Embedding request timeout. |
| `NORMALIZE_VECTORS` | `true` | Normalize query vectors. |
| `DEVICE` / `TORCH_DTYPE` | `auto` / `auto` | HuggingFace device/precision. |

### Inheritance from EKIE — `EKRE_INHERITANCE__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `ALLOW_CONFIG_FALLBACK` | `true` | Allow fallbacks when a value cannot be inherited. |
| `FALLBACK_EMBEDDING_MODEL` | *(blank)* | Fallback embedding model. |
| `FALLBACK_DIMENSION` | `0` | Fallback vector dimension. |
| `FALLBACK_DISTANCE_METRIC` | `cosine` | Fallback distance metric. |

### Security ingress — `EKRE_SECURITY__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `REQUIRE_SECURITY_CONTEXT` | `true` | Every request must carry a valid security context. |
| `DEFAULT_CLEARANCE` | `public` | Default clearance level. |

### Query intelligence — `EKRE_QUERY__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `MAX_QUERY_LENGTH` | `2048` | Maximum query length. |
| `DEFAULT_LANGUAGE` | `en` | Default language. |
| `CANDIDATE_COUNT_PRECISION` / `_RECALL` / `_BALANCED` / `_COMPLIANCE` / `_PERFORMANCE` | `5` / `50` / `20` / `30` / `10` | Candidate count per retrieval profile. |
| `ENABLE_LLM_INTERPRETER` | `false` | Optional LangChain query interpreter (deterministic fallback). |
| `LLM_PROVIDER` / `LLM_MODEL` / `LLM_BASE_URL` / `LLM_TEMPERATURE` / `LLM_REQUEST_TIMEOUT_SECONDS` | `huggingface` / *(blank)* / `http://localhost:11434` / `0.0` / `60.0` | Interpreter model config. |

### Execution core — `EKRE_EXECUTION__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `RUNNER` | `concurrent` | `concurrent` (default) or `langgraph`. |
| `MAX_PARALLEL_WORKERS` | `4` | Thread-pool size. |
| `DEFAULT_TASK_TIMEOUT_MS` | `150.0` | Per-task timeout fallback. |
| `MAX_ATTEMPTS_PER_TASK` | `1` | Bounded retries per task. |
| `ADMISSION_ENABLED` | `true` | Admission control. |
| `FAIL_OPEN` | `true` | All-worker failure returns empty instead of raising. |
| `ENABLE_TRACING` | `false` | LangGraph/Langfuse tracing toggle. |

### Retrieval workers — `EKRE_WORKERS__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `CONNECTOR` | `inmemory` | `inmemory` (offline) or `qdrant` (live vector store). |
| `QUERY_EMBEDDER` | `local_hash` | `local_hash` (deterministic offline) or `langchain` (inherited EKIE model). |
| `LOCAL_EMBEDDING_DIMENSION` | `256` | Dimension for the offline hash embedder. |

### Candidate fusion — `EKRE_FUSION__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `IDENTITY_POLICY` | `chunk` | `chunk`, `document`, or `strict` identity grouping. |
| `RRF_K` | `60` | Reciprocal Rank Fusion constant. |

### Ranking — `EKRE_RANKING__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `CANDIDATE_LIMIT` | `10` | Top-N ranked objects. |
| `MIN_COMPOSITE_SCORE` | `0.0` | Minimum composite score to keep. |
| `SEMANTIC_WEIGHT` / `LEXICAL_WEIGHT` / `METADATA_WEIGHT` / `FUSION_WEIGHT` | `0.4` / `0.2` / `0.1` / `0.3` | Evidence factor weights. |
| `POLICY_VERSION` | `v1` | Versioned aggregation strategy. |
| `ENABLE_LLM_RERANKER` | `false` | Optional LangChain reranker (deterministic fallback). |
| `LLM_PROVIDER` / `LLM_MODEL` / `LLM_BASE_URL` / `LLM_TEMPERATURE` / `LLM_REQUEST_TIMEOUT_SECONDS` | `huggingface` / *(blank)* / `http://localhost:11434` / `0.0` / `60.0` | Reranker model config. |

### Context assembly — `EKRE_ASSEMBLY__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `MAX_CONTEXT_TOKENS` | `4000` | Token budget for the handoff package. |
| `MAX_OBJECTS` | `10` | Maximum knowledge objects. |
| `ORDERING` | `rank` | `rank` (relevance) or `document` (by document/chunk). |
| `NORMALIZE_WHITESPACE` | `true` | Whitespace optimization. |
| `DEDUPE_CONTENT` | `true` | Drop duplicate content. |
| `CHARS_PER_TOKEN` | `4` | Token estimate ratio. |
| `MIN_RELEVANCE` | `0.0` | Minimum relevance to include. |

### Governance — `EKRE_GOVERNANCE__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `ENABLE_AUDIT` | `true` | Audit every authorization decision. |
| `AUDIT_SINK` | `logging` | `logging` or `memory`. |
| `ENABLE_MASKING` | `true` | Mask PII before the EKCP handoff. |
| `MASK_EMAIL` / `MASK_PHONE` / `MASK_SSN` / `MASK_CREDIT_CARD` | `true` | PII categories to redact. |
| `TOTAL_LATENCY_BUDGET_MS` | `500.0` | Trace over-budget threshold. |
| `POLICY_VERSION` | `v1` | Governance policy version. |

### Deployment & NFR — `EKRE_DEPLOYMENT__`
| Variable | Default | Purpose |
| --- | --- | --- |
| `VECTOR_POOL_SIZE` / `KEYWORD_POOL_SIZE` / `METADATA_POOL_SIZE` | `4` / `2` / `2` | Capability-grouped worker pools. |
| `REPLICAS` | `2` | Replica count for availability. |
| `CIRCUIT_BREAKER_THRESHOLD` | `5` | Failures before the breaker trips open. |
| `CIRCUIT_BREAKER_RESET_SECONDS` | `30.0` | Half-open probe delay. |
| `TENANT_MAX_CONCURRENT` | `8` | Per-tenant concurrency ceiling (0 = unlimited). |
| `MAX_LATENCY_MS` | `500.0` | NFR latency target. |
| `MIN_AVAILABILITY` | `0.999` | NFR availability target. |
| `EVAL_K` | `10` | k for accuracy metrics. |
| `MIN_PRECISION_AT_K` / `MIN_RECALL_AT_K` / `MIN_MRR` / `MIN_NDCG` | `0.5` | Accuracy thresholds. |

---

## 5. Inheritance From EKIE

EKRE must query the **same** collection with the **same** embedding model and
distance metric EKIE used to create the stored vectors — you can only search
vectors with the identical model and metric that produced them.

- **Distance metric + dimension** are read from the live Qdrant collection schema.
- **Embedding model** is read from the vector payload metadata (`embedding_model`).
- Configured fallbacks (`EKRE_INHERITANCE__FALLBACK_*`) apply only when a value
  cannot be resolved and `ALLOW_CONFIG_FALLBACK=true`.

Inspect the resolved profile at any time:

```powershell
curl http://127.0.0.1:8002/v1/retrieval/config -Headers @{ "X-Tenant-ID" = "tenant-a" }
# Returns collection, embedding_provider, embedding_model, dimension, distance_metric,
# source ("inherited" | "hybrid" | "fallback"), search_type, default_top_k, latency_budgets_ms.
```

`source=fallback` means EKRE could not reach the collection (e.g. offline, or EKIE
has not published yet) and is reporting the configured fallback.

---

## 6. Starting The Service

```powershell
# cwd-safe launcher (works from any directory):
Push-Location services/ekre; ..\..\.venv\Scripts\python.exe scripts/start_api.py; Pop-Location

# Or, after pip install -e services/ekre[...]:
ekre-api
```

The API listens on `http://127.0.0.1:8002`. Interactive OpenAPI docs are at
`http://127.0.0.1:8002/docs`.

---

## 7. Verification Checklist

```powershell
# 1. Liveness / readiness
curl http://127.0.0.1:8002/health/live     # {"status":"ok","service":"ekre"}
curl http://127.0.0.1:8002/health/ready    # {"status":"ready","service":"ekre"}

# 2. Deployment readiness assessment
curl http://127.0.0.1:8002/v1/readiness

# 3. Resolved retrieval config (inheritance proof)
curl http://127.0.0.1:8002/v1/retrieval/config -Headers @{ "X-Tenant-ID" = "tenant-a" }

# 4. Full pipeline smoke test (empty in-memory connector -> valid empty package)
$body = '{"query":"compare EKIE and EKRE","security_context":{"user_id":"u1","tenant_id":"tenant-a","classification_clearance":"internal"}}'
curl -Method POST http://127.0.0.1:8002/v1/query/retrieve `
  -Headers @{ "X-Tenant-ID" = "tenant-a"; "Content-Type" = "application/json" } `
  -Body $body
```

Offline validation (no server) — run the per-stage demos:

```powershell
.\.venv\Scripts\python.exe services/ekre/scripts/demo_foundations.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_query_intelligence.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_execution.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_retrieval.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_fusion.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_ranking.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_assembly.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_governance.py
.\.venv\Scripts\python.exe services/ekre/scripts/demo_readiness.py
```

Static + test gate (from the repository root):

```powershell
.\.venv\Scripts\python.exe -m ruff check services/ekre
Push-Location services/ekre; ..\..\.venv\Scripts\python.exe -m mypy src; Pop-Location
Push-Location services/ekre; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location
```

---

## 8. Production Hardening

In `services/ekre/.env`:

```ini
# Query the live vector store EKIE published to, with the inherited model.
EKRE_WORKERS__CONNECTOR=qdrant
EKRE_WORKERS__QUERY_EMBEDDER=langchain
EKRE_QDRANT__HOST=<qdrant-host>
EKRE_QDRANT__PORT=6333

# Enforce security context on every request (default).
EKRE_SECURITY__REQUIRE_SECURITY_CONTEXT=true

# Compliance: mask PII before the EKCP handoff (default).
EKRE_GOVERNANCE__ENABLE_MASKING=true
EKRE_GOVERNANCE__ENABLE_AUDIT=true
EKRE_GOVERNANCE__AUDIT_SINK=logging

# Observability: enable self-hosted Langfuse tracing.
EKRE_OBSERVABILITY__LANGFUSE_ENABLED=true
EKRE_OBSERVABILITY__LANGFUSE_HOST=http://localhost:3000
EKRE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY=<key>
EKRE_OBSERVABILITY__LANGFUSE_SECRET_KEY=<key>

# NFR thresholds validated for EKCP handoff readiness.
EKRE_DEPLOYMENT__MAX_LATENCY_MS=500.0
EKRE_DEPLOYMENT__MIN_PRECISION_AT_K=0.5
```

The embedding **provider** must be able to load the same model EKIE used; the
model name, dimension, and distance metric are inherited automatically — never
hardcode them.

---

## 9. Troubleshooting

| Symptom | Cause | Resolution |
| --- | --- | --- |
| `/v1/query/*` returns an empty package | Default in-memory connector has no data, or EKIE has not published. | Set `EKRE_WORKERS__CONNECTOR=qdrant` + `QUERY_EMBEDDER=langchain` and confirm EKIE published to the collection. |
| `/v1/retrieval/config` shows `source=fallback` | Collection unreachable at request time. | Verify Qdrant host/port and that the collection exists. |
| Dimension mismatch / zero results on the live path | Query embedded with a different model than EKIE used. | Ensure `EKRE_EMBEDDING__PROVIDER` loads the same model; rely on inheritance, do not hardcode. |
| `400` on `/v1/query/*` | Missing `X-Tenant-ID` header. | Send the tenant header. |
| `403` on `/v1/query/*` | Security context missing/invalid or tenant mismatch. | Provide a valid `security_context` whose `tenant_id` matches `X-Tenant-ID`. |
| Public user sees no restricted docs | Pre-pool clearance filtering (by design). | Expected — unauthorized candidates never enter the pool. |

---

See [EKRE-Help_Guide.md](EKRE-Help_Guide.md) for the complete API reference,
pipeline deep dive, and domain module documentation.

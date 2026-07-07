# EKRE — Enterprise Knowledge Retrieval Engine

## Complete Documentation & Operations Guide

> Companion documents: [EKRE-Deployment-Guide.md](EKRE-Deployment-Guide.md) (setup & config) and [EKRE-handbook.md](EKRE-handbook.md) (architecture). Sprint history: [../sprints/ekre-sprint-track.md](../sprints/ekre-sprint-track.md).

## Table of Contents
1. [Introduction](#1-introduction)
2. [Architecture Overview](#2-architecture-overview)
3. [Project Structure](#3-project-structure)
4. [Configuration Reference](#4-configuration-reference)
5. [Running The Service](#5-running-the-service)
6. [API Reference](#6-api-reference)
7. [Retrieval Pipeline Stages](#7-retrieval-pipeline-stages)
8. [Domain Modules Deep Dive](#8-domain-modules-deep-dive)
9. [Security, Governance & Compliance](#9-security-governance--compliance)
10. [Observability & Tracing](#10-observability--tracing)
11. [NFR Validation & Readiness](#11-nfr-validation--readiness)
12. [The EKCP Handoff](#12-the-ekcp-handoff)
13. [LangChain / LangGraph Integration](#13-langchain--langgraph-integration)
14. [Demo Scripts](#14-demo-scripts)

---

## 1. Introduction

EKRE is the **retrieval** engine of the Enterprise Knowledge Platform. It
transforms a user query into ranked, citation-preserving, policy-compliant
context — the `RetrievalContextPackage` handed to EKCP for response generation.

**EKRE owns:** query understanding, planning, retrieval execution and workers,
candidate fusion, ranking, and context assembly, plus cross-cutting observability,
security, and compliance.

**EKRE does not own:** knowledge ingestion and embedding generation (EKIE), or
response generation, prompts, and conversation memory (EKCP).

Guiding principles: knowledge stays immutable; retrieval is deterministic
(the same query against the same knowledge state yields identical results);
security is enforced before relevance; hybrid retrieval; every decision is
explainable and observable; ranking is separate from retrieval; retrieval is
model-independent and inherits its embedding model and distance metric from EKIE.

---

## 2. Architecture Overview

```
User Query
   │
   ▼  Query Intelligence (S1) ── understanding → intent → enrichment → plan
   ▼  Retrieval Execution (S2) ── orchestrator + scheduler + runner (parallel, fail-open)
   ▼  Retrieval Workers (S3) ──── vector / keyword / metadata via repository connectors
   │                              (security clearance filter at the data boundary)
   ▼  Candidate Fusion (S4) ───── unified collection + Reciprocal Rank Fusion → Knowledge Objects
   ▼  Ranking (S5) ────────────── evidence-weighted, auditable, optional LLM reranker
   ▼  Context Assembly (S6) ───── token-budgeted selection → RetrievalContextPackage
   │
   └── Cross-cutting (S7): end-to-end trace + immutable audit + PII masking
   └── Readiness (S8): resilience, multi-tenancy, accuracy/latency validation

RetrievalContextPackage ──► EKCP (response generation)
```

Everything is deterministic and local-first by default. LangChain/LangGraph and
real vector/model clients are config-selected behind engine-owned seams; the
offline path never loads them.

---

## 3. Project Structure

```
services/ekre/
├── pyproject.toml            # ruff + mypy strict, pytest, optional-deps extras
├── .env.example              # full EKRE_* configuration template
├── src/
│   ├── config/settings.py    # EkreSettings (all EKRE_* groups) + get_settings()
│   ├── composition.py        # build_* factories (the single wiring point)
│   ├── api/                  # FastAPI app, middleware, routers
│   └── domain/
│       ├── observability/    # context (tenant/correlation/query id), JSON logging, latency
│       ├── security/         # security-context ingress validation
│       ├── inheritance/      # embedding/distance inheritance from EKIE metadata
│       ├── integrations/     # LangChain seam: embeddings, chat, Qdrant, retriever
│       ├── query/            # S1 query intelligence (understanding→intent→enrich→plan)
│       ├── execution/        # S2 orchestrator, scheduler, worker framework, runners
│       ├── connectors/       # repository connector framework (in-memory + Qdrant)
│       ├── retrieval/        # S3 vector/keyword/metadata workers + embedding + security filter
│       ├── fusion/           # S4 unified collection + RRF fusion
│       ├── ranking/          # S5 ranking engine + optional reranker
│       ├── assembly/         # S6 context assembly + packaging
│       ├── governance/       # S7 trace + audit + masking + traced pipeline
│       ├── resilience/       # S8 circuit breaker + tenant concurrency limiter
│       ├── evaluation/       # S8 accuracy metrics + harness
│       └── readiness/        # S8 deployment + EKCP handoff readiness
├── scripts/                  # start_api.py + one demo per sprint
└── tests/                    # 162 tests, ruff + mypy strict clean
```

---

## 4. Configuration Reference

All configuration is environment-backed with the `EKRE_` prefix and nested `__`
delimiter (see the full table in the
[Deployment Guide §4](EKRE-Deployment-Guide.md#4-configuration-reference)).
Configuration groups: `QDRANT__`, `OBSERVABILITY__`, `RETRIEVAL__`, `EMBEDDING__`,
`INHERITANCE__`, `SECURITY__`, `QUERY__`, `EXECUTION__`, `WORKERS__`, `FUSION__`,
`RANKING__`, `ASSEMBLY__`, `GOVERNANCE__`, `DEPLOYMENT__`, plus the top-level
`EKRE_APP_NAME` and `EKRE_ENVIRONMENT`.

Nothing is hardcoded. The embedding model, dimension, and distance metric are
inherited from EKIE at runtime; every operational value is a configuration knob.

---

## 5. Running The Service

```powershell
# Start the API (port 8002; cwd-safe launcher):
Push-Location services/ekre; ..\..\.venv\Scripts\python.exe scripts/start_api.py; Pop-Location
# Or, after pip install -e services/ekre[...]:  ekre-api

# Health probes:
curl http://127.0.0.1:8002/health/live     # {"status":"ok","service":"ekre"}
curl http://127.0.0.1:8002/health/ready    # {"status":"ready","service":"ekre"}

# OpenAPI docs:  http://127.0.0.1:8002/docs
```

Every request should carry `X-Tenant-ID` (required for query endpoints); an
`X-Correlation-ID` (and `X-Query-ID`) may be supplied for tracing and are
generated when absent. Both are echoed back on the response.

---

## 6. API Reference

Base URL: `http://127.0.0.1:8002`. Query endpoints require the `X-Tenant-ID`
header and a `security_context` whose `tenant_id` matches it.

### Health & readiness
| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health/live` | Liveness probe. |
| GET | `/health/ready` | Readiness probe. |
| GET | `/v1/readiness` | Deployment readiness assessment (pools, HA, resilience, tenancy, NFR targets). |
| GET | `/v1/retrieval/config` | Resolved retrieval profile inherited from EKIE (requires tenant header). |

### Query pipeline (progressive stages)
| Method | Path | Returns | Stage reached |
| --- | --- | --- | --- |
| POST | `/v1/query/plan` | `StructuredQuery` | S1 (plan) |
| POST | `/v1/query/execute` | `ExecutionSession` | S2–S3 (raw candidates) |
| POST | `/v1/query/candidates` | `FusedKnowledgeSet` | S4 (fused) |
| POST | `/v1/query/rank` | `RankedKnowledgeSet` | S5 (ranked) |
| POST | `/v1/query/context` | `AssemblyResult` | S6 (assembled package + metrics) |
| POST | `/v1/query/retrieve` | `TracedRetrieval` | S1–S7 (package + metrics + trace, audited & masked) |

All query endpoints share the same request body:

```json
{
  "query": "compare EKIE and EKRE architecture",
  "security_context": {
    "user_id": "analyst-1",
    "tenant_id": "tenant-a",
    "classification_clearance": "internal"
  },
  "language": null
}
```

Headers: `X-Tenant-ID: tenant-a` (required), `Content-Type: application/json`.

**Status codes:** `200` success; `400` missing `X-Tenant-ID`; `403` invalid
security context or tenant mismatch; `422` an unprocessable query or execution
error.

### `POST /v1/query/retrieve` — the production endpoint

Runs the complete pipeline with tracing, audit, and PII masking, returning a
`TracedRetrieval`:

```json
{
  "package": {
    "query": "...",
    "tenant_id": "tenant-a",
    "candidates": [
      { "citation": { "document_id": "...", "chunk_id": "...", "source_path": "..." },
        "content": "...", "relevance_score": 0.83, "explanation": "composite=..." }
    ],
    "security_filtered": true
  },
  "metrics": { "considered_count": 0, "selected_count": 0, "total_tokens": 0, "token_budget": 4000, "ordering": "rank" },
  "trace": {
    "execution_id": "exec-...", "trace_id": "...", "tenant_id": "tenant-a",
    "stages": [ { "stage": "query_understanding", "duration_ms": 0.25 }, ... ],
    "total_ms": 2.4, "budget_ms": 500.0, "over_budget": false, "redactions": 0, "policy_version": "v1"
  }
}
```

With the default in-memory connector (no indexed data), the package is a valid,
empty, citation-safe result; the trace and audit still fire.

---

## 7. Retrieval Pipeline Stages

| Sprint | Stage | Input → Output | Key models |
| --- | --- | --- | --- |
| S0 | Foundations | settings → resolved `EmbeddingProfile` | `SecurityContext`, `EmbeddingProfile` |
| S1 | Query Intelligence | raw query → `StructuredQuery` (understanding, intent, enrichment, plan) | `QueryUnderstanding`, `IntentClassification`, `RetrievalPlan` |
| S2 | Execution Core | plan → `ExecutionSession` (parallel, fail-open) | `RetrievalTask`, `WorkerOutcome`, `ExecutionSession` |
| S3 | Workers & Connectors | tasks → candidates (clearance-filtered) | `RepositoryDocument`, `RetrievalCandidate` |
| S4 | Fusion | outcomes → `FusedKnowledgeSet` (RRF) | `UnifiedCandidateSet`, `KnowledgeObject` |
| S5 | Ranking | fused → `RankedKnowledgeSet` | `RankedKnowledgeObject` |
| S6 | Context Assembly | ranked → `RetrievalContextPackage` | `AssemblyResult`, `ContextMetrics` |
| S7 | Governance | package → traced/audited/masked | `RetrievalTrace`, `AuditRecord` |
| S8 | Readiness | — → readiness/accuracy reports | `ReadinessReport`, `EvaluationReport` |

### S1 — Query Intelligence
Deterministic, immutable, explainable pipeline: **Query Understanding** (normalize,
detect language, extract entities/dates/numbers/metadata filters, resolve
enterprise acronyms), **Intent Classification** (8 enterprise intents → retrieval
profile + candidate count), **Enrichment** (synonym/vocabulary expansion), and the
**Query Planner** (selects vector/keyword/metadata engines, candidate limits,
timeouts, ranking strategy). Every stage records a `Transformation` for
explainability. An optional LangChain LLM interpreter refines understanding only,
with a graceful deterministic fallback.

### S2 — Retrieval Execution Core
The orchestrator consumes a `RetrievalPlan`, the scheduler applies admission
control and deterministic priority, and the runner executes workers in parallel
(default `ConcurrentExecutionRunner`; optional `LangGraphExecutionRunner`). Failed
or timed-out workers are isolated into `WorkerOutcome`s; `fail_open` returns an
empty result on total failure rather than aborting. Results are returned in input
order for determinism.

### S3 — Retrieval Workers & Connectors
`VectorRetrievalWorker` embeds the query with the inherited model and searches
through a repository connector; `KeywordRetrievalWorker` does exact-term matching;
`MetadataRetrievalWorker` matches structured attributes. Workers talk only to
connectors (`InMemoryRepositoryConnector` offline, `QdrantRetrievalConnector`
live). The **clearance filter is applied at the connector (data) boundary**, so
unauthorized candidates never enter the pool; a defense-in-depth post-filter
guarantees it.

### S4 — Candidate Fusion
The **Unified Candidate Collection** aggregates raw per-worker candidates with
provenance (no dedup, no ranking). **Candidate Fusion** groups same-asset
candidates (chunk/document/strict identity), aggregates their evidence, and
computes a deterministic **Reciprocal Rank Fusion** score into `KnowledgeObject`s
— one per asset, every evidence source preserved.

### S5 — Ranking
Eligibility filter → per-factor evidence scoring (semantic/lexical/metadata/fusion)
→ configurable weighted composite → deterministic ordering → top-N. Each
`RankedKnowledgeObject` carries the full audit trail (factor scores, weights,
composite, explanation, policy version). An optional LangChain reranker refines
the order with a deterministic fallback.

### S6 — Context Assembly
Selects ranked objects within a token budget (dedup, relevance threshold, object
cap), orders them (rank or document), and packages the immutable
`RetrievalContextPackage`. **Citation lineage is never dropped.** `ContextMetrics`
records considered/selected counts, tokens vs budget, and drop accounting.

---

## 8. Domain Modules Deep Dive

| Module | Responsibility |
| --- | --- |
| `domain/observability` | Context vars (tenant/correlation/query id), structured JSON logging, `LatencyRecorder`, Langfuse callback seam. |
| `domain/security` | `SecurityContextValidator` — ingress validation of the `SecurityContext` contract. |
| `domain/inheritance` | `InheritanceResolver` + `QdrantSchemaReader` — resolve embedding model/dimension/distance metric from EKIE. |
| `domain/integrations` | `build_embeddings` / `build_chat_model` / `build_qdrant_client` / `build_qdrant_vector_store` / `build_retriever` — the single provider-agnostic LangChain seam. |
| `domain/query` | Query understanding, intent, enrichment, planner, pipeline, optional LLM interpreter. |
| `domain/execution` | Orchestrator, scheduler, worker framework (ABC + registry + lifecycle), runners. |
| `domain/connectors` | Repository connector framework: `RepositoryConnector` ABC, in-memory, Qdrant. |
| `domain/retrieval` | Vector/keyword/metadata workers, embedding adapters, pre-pool security filter, worker-registry factory. |
| `domain/fusion` | `CandidateCollector` (UCS) + `CandidateFusion` (RRF → FKS). |
| `domain/ranking` | `RankingEngine`, scoring, optional reranker. |
| `domain/assembly` | `ContextAssemblyEngine`, token estimation, selection, citation builder. |
| `domain/governance` | `RetrievalTrace`, audit trail, PII `Masker`, the traced `RetrievalPipeline`. |
| `domain/resilience` | `CircuitBreaker`, `TenantConcurrencyLimiter`. |
| `domain/evaluation` | Precision@k / Recall@k / MRR / NDCG metrics + `evaluate` harness. |
| `domain/readiness` | Deployment + EKCP handoff readiness assessments. |

The `composition.py` root is the single place that reads settings and wires these
modules together via `build_*` factories; domain packages stay independent of the
settings module.

---

## 9. Security, Governance & Compliance

- **Security context ingress** — every query must carry a valid `SecurityContext`
  (user, tenant, clearance); tenant mismatch is rejected with `403`.
- **Pre-pool clearance filtering** — the set of clearances a principal may see is
  computed from the context and pushed into the connector, so unauthorized
  documents never leave the repository layer; a post-filter enforces it again.
- **Immutable audit trail** — every authorization decision is recorded as an
  `AuditRecord` (actor, clearance, outcome, execution id, policy version) to the
  configured `AuditSink` (`logging` or `memory`).
- **PII masking** — email, phone, SSN, and credit-card patterns are redacted from
  candidate content before the EKCP handoff; citation lineage is never altered and
  the redaction count is recorded in the trace.

---

## 10. Observability & Tracing

- **Structured JSON logs** carry `tenant_id`, `correlation_id`, and `query_id` on
  every record.
- **`RetrievalTrace`** records the per-stage execution timeline
  (`query_understanding`, `execution`, `fusion`, `ranking`, `assembly`, `masking`)
  with a latency breakdown, total, budget, and over-budget flag, plus
  execution/trace/correlation ids.
- **Langfuse** tracing is available behind a lazy seam and points to the local
  self-hosted instance only.
- **Latency budgets** are configuration-driven (`EKRE_RETRIEVAL__BUDGET_*`,
  `EKRE_GOVERNANCE__TOTAL_LATENCY_BUDGET_MS`).

---

## 11. NFR Validation & Readiness

- **Accuracy** — `domain/evaluation` computes Precision@k, Recall@k, MRR, and NDCG
  against a labeled judgment set and checks configured thresholds.
- **Resilience** — `CircuitBreaker` (closed/open/half-open) isolates a repeatedly
  failing dependency; `fail_open` provides graceful degradation.
- **Multi-tenancy** — `TenantConcurrencyLimiter` enforces a per-tenant concurrency
  ceiling so no tenant exhausts shared capacity.
- **Readiness** — `assess_deployment_readiness` (pools, replicas, resilience,
  tenancy, NFR targets) and `assess_handoff_readiness` (citation persistence,
  `security_filtered`, latency budget, accuracy thresholds). The deployment report
  is served at `GET /v1/readiness`.

---

## 12. The EKCP Handoff

The `RetrievalContextPackage` (defined in `packages/contracts`) is the **only**
artifact EKRE hands to EKCP:

```python
class RetrievalContextPackage(VersionedContract):
    query: str
    tenant_id: str
    candidates: list[RetrievalCandidate]   # each with a preserved Citation + explanation
    security_filtered: bool
```

Each `RetrievalCandidate` carries a `Citation` (`document_id`, `chunk_id`,
`source_path`), the (masked) content, a relevance score, and a ranking
explanation. Citation lineage is guaranteed to survive the entire pipeline.

---

## 13. LangChain / LangGraph Integration

`domain/integrations/langchain_resources.py` is the single, provider-agnostic
seam for all LangChain resources across EKRE:

- `build_embeddings(provider, model, ...)` — HuggingFace or Ollama query embedding.
- `build_chat_model(provider, model, ...)` — HuggingFace or Ollama chat model
  (used by the optional query interpreter and reranker).
- `build_qdrant_client` / `build_qdrant_vector_store` / `build_retriever` — Qdrant
  connection and the LCEL retriever (`vector_store.as_retriever(...)`).

All imports are lazy so the offline path never loads LangChain. The provider and
model are **inherited from EKIE / set per use case** — never hardcoded. LangGraph
is the optional execution runner; deterministic engines remain the default. LLM
stages (query interpreter, reranker) are feature-flagged off with deterministic
fallbacks, so enabling them can only help, never break determinism.

---

## 14. Demo Scripts

Each sprint ships an offline demo under `services/ekre/scripts/`:

```powershell
.\.venv\Scripts\python.exe services/ekre/scripts/demo_foundations.py        # S0 config/inheritance/security
.\.venv\Scripts\python.exe services/ekre/scripts/demo_query_intelligence.py # S1 query plan
.\.venv\Scripts\python.exe services/ekre/scripts/demo_execution.py          # S2 parallel + graceful degradation
.\.venv\Scripts\python.exe services/ekre/scripts/demo_retrieval.py          # S3 workers + clearance filtering
.\.venv\Scripts\python.exe services/ekre/scripts/demo_fusion.py             # S4 RRF fusion
.\.venv\Scripts\python.exe services/ekre/scripts/demo_ranking.py            # S5 ranking audit trail
.\.venv\Scripts\python.exe services/ekre/scripts/demo_assembly.py           # S6 handoff package
.\.venv\Scripts\python.exe services/ekre/scripts/demo_governance.py         # S7 trace + audit + masking
.\.venv\Scripts\python.exe services/ekre/scripts/demo_readiness.py          # S8 accuracy + readiness
```

All demos run fully offline (in-memory connector + deterministic hash embedder).

---

For setup, configuration tables, and production hardening, see
[EKRE-Deployment-Guide.md](EKRE-Deployment-Guide.md). For architecture and design
rationale, see [EKRE-handbook.md](EKRE-handbook.md).

# EKCP — Enterprise Knowledge Chat Platform

## Complete Documentation & Operations Guide

> **Version:** 1.0
> **Status:** Approved (Phase 0 through EKCP-S8)
> **Audience:** Engineers, DevOps, Platform Operators
> **Last Updated:** 2026-07-08

> Companion documents: [EKCP-Deployment-Guide.md](EKCP-Deployment-Guide.md) (setup & configuration) and [EKCP-handbook.md](EKCP-handbook.md) (architecture). Sprint history: [../sprints/ekcp-sprint-track.md](../sprints/ekcp-sprint-track.md).

## Table of Contents

1. [Introduction](#1-introduction)
2. [Architecture Overview](#2-architecture-overview)
3. [Project Structure](#3-project-structure)
4. [Configuration Reference](#4-configuration-reference)
5. [Running The Service](#5-running-the-service)
6. [API Reference](#6-api-reference)
7. [Conversation Pipeline Stages](#7-conversation-pipeline-stages)
8. [Domain Modules Deep Dive](#8-domain-modules-deep-dive)
9. [Security, Governance & Compliance](#9-security-governance--compliance)
10. [Memory Framework](#10-memory-framework)
11. [Observability & Tracing](#11-observability--tracing)
12. [Resilience & Knowledge Integration](#12-resilience--knowledge-integration)
13. [NFR Validation & Readiness](#13-nfr-validation--readiness)
14. [The Master Integration Handoff](#14-the-master-integration-handoff)
15. [LangChain / LangGraph Integration](#15-langchain--langgraph-integration)
16. [Demo Scripts](#16-demo-scripts)
17. [Testing](#17-testing)
18. [Troubleshooting](#18-troubleshooting)
19. [Glossary](#19-glossary)

---

## 1. Introduction

EKCP is the **conversation and response-generation** engine of the Enterprise
Knowledge Platform. It turns a user message into a governed, grounded,
policy-compliant response — orchestrating conversation state, intent, context,
prompts, model invocation, memory, agents, and workflows.

**EKCP owns:** the conversation lifecycle (Conversation Digital Twin), intent
gating, context assembly, prompt orchestration, the model gateway, the memory
framework, agent/tool/planning runtime, governance enforcement, workflow
orchestration, and readiness.

**EKCP does not own:** knowledge ingestion and embedding (EKIE), or retrieval and
ranking (EKRE). EKCP *consumes* EKRE's `RetrievalContextPackage` as one context
source.

Guiding principles: intent is resolved before execution; context is assembled
before generation; security is enforced before relevance; every model call goes
through a single governed gateway; every governed operation is authorized and
audited; the engine is model-independent (LangChain/LangGraph live behind seams);
and the default path is deterministic and local-first.

---

## 2. Architecture Overview

```
User Message
   │
   ▼  Conversation Core (S1) ──── Conversation Digital Twin + session + Intent Gate
   ▼  Context Assembly (S2) ───── ranked, token-bounded Execution Context Package
   ▼  Prompt Orchestration (S2) ─ declarative layered templates → Prompt Package
   ▼  Model Gateway (S3) ──────── single governed boundary → normalized response
   │        ├─ Memory Framework (S4): 6 tiers feed context + persist outcomes
   │        ├─ Agents/Tools/Planning (S5): permission-gated bounded execution
   │        └─ Knowledge (S7): EKRE via circuit breaker (degrades to memory)
   │
   └── Cross-cutting Governance (S6): RBAC/ABAC + audit + masking + redaction
   └── Workflow & Events (S7): objective → plan → lifecycle + platform events
   └── Readiness (S8): deployment + multi-tenancy + master handoff KPIs

Response ──► Web UI (SSE stream) / API client
```

Everything is deterministic and local-first by default. LangChain/LangGraph and
real chat/knowledge/cache/control-plane clients are configuration-selected behind
engine-owned seams; the offline path never loads them.

---

## 3. Project Structure

```
services/ekcp/
├── pyproject.toml            # ruff + mypy strict, pytest, optional-deps extras
├── .env.example              # full EKCP_* configuration template
├── src/
│   ├── config/settings.py    # EkcpSettings (all EKCP_* groups) + get_settings()
│   ├── composition.py        # build_* factories (the single wiring point)
│   ├── api/                  # FastAPI app, correlation middleware, routers
│   └── domain/
│       ├── observability/    # context (tenant/correlation/session id), JSON logging, latency, tracing
│       ├── security/         # security-context ingress validation
│       ├── conversation/     # Conversation Digital Twin lifecycle + store + events
│       ├── session/          # session lifecycle + store
│       ├── intent/           # deterministic intent classification + gate
│       ├── context/          # Execution Context Package assembly + budgeting
│       ├── prompt/           # declarative prompt templates + orchestrator + citations
│       ├── integrations/     # LangChain seam: build_chat_model
│       ├── gateway/          # model registry/selector/providers + LLM gateway + budgets
│       ├── memory/           # 6-tier memory framework + retrieval + retention
│       ├── tools/            # tool registry + permission gate + executor
│       ├── agents/           # agent registry/selector + runtime + coordinator
│       ├── planning/         # rule-based planning engine + task DAG
│       ├── governance/       # RBAC/ABAC policy engine + guard + audit + masking + redaction
│       ├── knowledge/        # EKRE client + circuit breaker + graceful degradation
│       ├── workflow/         # workflow orchestrator + platform events
│       └── readiness/        # deployment + tenancy + master handoff assessments
├── scripts/                  # start_api.py + one demo per sprint
└── tests/                    # 172 tests, ruff + mypy --strict clean (133 source files)
```

---

## 4. Configuration Reference

All configuration is environment-backed with the `EKCP_` prefix and nested `__`
delimiter. Nothing is hardcoded — the chat model, backends, budgets, weights,
identities, and KPI targets are all configuration knobs. The offline default is
fully in-memory and dependency-free.

Configuration groups: `GATEWAY__`, `OBSERVABILITY__`, `SECURITY__`, `REDIS__`,
`CONTROL_PLANE__`, `CONVERSATION__`, `SESSION__`, `INTENT__`, `CONTEXT__`,
`PROMPT__`, `MODEL__`, `MEMORY__`, `TOOLS__`, `AGENT__`, `PLANNING__`,
`GOVERNANCE__`, `KNOWLEDGE__`, `WORKFLOW__`, `DEPLOYMENT__`, plus the top-level
`EKCP_APP_NAME` and `EKCP_ENVIRONMENT`.

See the full per-variable table in the
[Deployment Guide §5](EKCP-Deployment-Guide.md#5-configuration-reference) and the
template at [../../services/ekcp/.env.example](../../services/ekcp/.env.example).

---

## 5. Running The Service

```powershell
# Offline default path (no external dependencies).
.\.venv\Scripts\python.exe services/ekcp/scripts/start_api.py
```

The server binds `EKCP_GATEWAY__HOST:PORT` (default `0.0.0.0:8003`). Enable live
backends (chat model, EKRE knowledge, Redis, SQL Server) via configuration — see
[Deployment Guide §6](EKCP-Deployment-Guide.md#6-selecting-backends).

**Standard headers** (bound by the correlation middleware):

| Header | Required | Purpose |
|---|---|---|
| `X-Tenant-ID` | Yes (governed routes) | Tenant scope for isolation and logging. |
| `Authorization` / `X-Service-Token` | When gateway auth is enabled | Shared bearer token proving the request comes from the trusted gateway. |
| `X-Correlation-ID` | No (generated if absent) | End-to-end request tracing. |
| `X-Session-ID` | No | Conversation session correlation. |

---

## 6. API Reference

All request/response bodies are Pydantic v2 models. Governed routes require the
`X-Tenant-ID` header and a `security_context` whose `tenant_id` matches it;
otherwise the ingress gate returns `403`. Base URL: `http://localhost:8003`.

### 6.1 Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health/live` | Liveness. Returns `{status:"ok",service:"ekcp"}`. |
| `GET` | `/health/ready` | Readiness. Returns `{status:"ready",service:"ekcp"}`. |

### 6.2 Conversation

**`POST /conversation/start`** — start a conversation and open a session.

```json
{
  "security_context": {"user_id": "u1", "tenant_id": "tenant-a", "classification_clearance": "internal"},
  "title": "Quarterly review",
  "workspace_id": "default",
  "participants": []
}
```
Response: `{conversation_id, session_id, state}`.

**`POST /conversation/message`** — add a user message and run the governed loop.

```json
{
  "conversation_id": "...",
  "session_id": "...",
  "message": "Summarize Q3 revenue",
  "security_context": {"user_id": "u1", "tenant_id": "tenant-a", "classification_clearance": "internal"}
}
```
Response: `{interaction_id, conversation_state, intent, scope, confidence, requires_clarification, clarification_prompt, routing_target, assistant_response}`.

### 6.3 Context

**`POST /context/build`** — assemble the Execution Context Package.

Key fields: `conversation_id`, `user_intent`, `security_context`,
`conversation_history[]`, `knowledge[]` (inline candidates), `policy_constraints[]`,
`include_memory` (recall memory), `include_knowledge` (fetch from EKRE).
Response: `{context_id, conversation_id, selected_count, total_tokens, source_diversity, compression_applied, degraded, warnings[]}`.

### 6.4 Prompt

**`POST /prompt/generate`** — build a validated Prompt Package from a context.

Fields: `context_id`, `security_context`, `template_id?`, `output_format?`.
Response: `{prompt_id, prompt_text, template_id, template_version, token_estimate, validation_status, compression_applied}`.

### 6.5 Model

**`POST /model/invoke`** — invoke a model through the governed gateway. Supply
either `prompt_text` or a `context_id` (the prompt is then constructed).

Fields: `security_context`, `prompt_text?`, `context_id?`, `template_id?`,
`model_id?`, `response_type` (default `markdown`), `conversation_id?`.
Response: `{model_id, provider, output, response_type, token_usage:{prompt_tokens,completion_tokens,total_tokens}, latency_ms, cost_estimate, fallback_used}`.
Errors: `413` token-limit, `402` budget-exceeded, `502` provider/fallback, `503` model-unavailable.

### 6.6 Memory

| Method | Path | Body → Response |
|---|---|---|
| `POST` | `/memory/store` | `{content, memory_type, scope, validation_method, topic, tags[], conversation_id?, user_id?}` → `{memory_id, scope, confidence, expires_at}` |
| `POST` | `/memory/retrieve` | `{query, scopes?, limit?, min_confidence?}` → `{hits:[{memory_id, content, scope, memory_type, score, confidence}]}` |
| `POST` | `/memory/consolidate` | `{conversation_id, level}` → `{memory_id, content, source_count}` |
| `POST` | `/memory/purge` | `{user_id?, conversation_id?, reason}` → `{deleted_count}` |

All memory routes require `security_context` and the appropriate permission
(`READ_MEMORY` / `WRITE_MEMORY`).

### 6.7 Agent

**`POST /agent/execute`** — select an agent by capability and run it (authorizes
`INVOKE_AGENT`, masks the result).

Fields: `security_context`, `task_description`, `capability`, `prompt_text?`,
`granted_permissions[]`, `roles[]`.
Response: `{agent_id, status, result, confidence_score, model_used, steps, tool_usage[], recommended_next_actions[]}`.

**`POST /agent/plan`** — decompose an objective into an ordered plan.

Fields: `security_context`, `objective`.
Response: `{plan_id, objective, execution_strategy, tasks:[{task_id, description, required_capability, dependencies[], approval_required, priority}], approval_checkpoints[]}`.

### 6.8 Governance

**`POST /governance/evaluate`** — evaluate (without executing) a policy decision.

Fields: `security_context`, `permission`, `resource`, `resource_classification`
(default `internal`), `roles[]`.
Response: `{allowed, reason, policy_version}`.

**`GET /governance/audit`** — return the tenant's audit trail (in-memory sink only).
Response: `{records:[{event_id, action, result, actor, resource, reason}], total}`.

### 6.9 Workflow

| Method | Path | Description |
|---|---|---|
| `POST` | `/workflow/trigger` | `{objective}` → trigger + plan. Returns `{workflow_id, state, plan_id, task_count, version_number}`. |
| `GET` | `/workflow/{workflow_id}` | Return current workflow state. |
| `POST` | `/workflow/{workflow_id}/pause` | Pause an active workflow. |
| `POST` | `/workflow/{workflow_id}/resume` | Resume a paused workflow. |
| `POST` | `/workflow/{workflow_id}/approve` | Record a human approval (waiting/paused only). |

### 6.10 Readiness

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/readiness` | Deployment readiness assessment. |
| `GET` | `/v1/readiness/tenancy` | Multi-tenant isolation readiness. |
| `GET` | `/v1/readiness/handoff` | Master integration handoff package. |

Readiness routes take no tenant header or body. Reports return
`{name, findings:[{check, severity, message}], ready}`.

### 6.11 Chat (SSE)

**`POST /chat/stream`** — stream a governed chat response as Server-Sent Events.

Fields: `message`, `security_context?`, `session_id?`.
Event frames (`event: <type>\ndata: <json>`):

- `token` — `{text}` incremental fragment.
- `citation` — `{doc, chunk, source}` (once knowledge integration is active).
- `done` — `{session_id, correlation_id, finish_reason, total_tokens, cost_estimate}`.
- `error` — `{error_type, message}`.

---

## 7. Conversation Pipeline Stages

A single governed turn flows through these stages:

1. **Ingress** — correlation middleware binds tenant/correlation/session ids; the
   security validator enforces the security context.
2. **Conversation Core** — the Conversation Digital Twin loads/advances through
   its lifecycle; the session is touched; the Intent Gate classifies intent and
   routes (personal → memory, organizational → knowledge) or requests
   clarification when confidence is below threshold.
3. **Context Assembly** — conversation history, recalled memory, and (optionally)
   EKRE knowledge are ranked, deduped, citation-checked, and token-bounded into an
   Execution Context Package.
4. **Prompt Orchestration** — declarative layered templates render a Prompt
   Package with explicit named variables (no hardcoded prompt strings).
5. **Model Gateway** — a single governed boundary selects a model, enforces token
   and cost budgets, invokes the provider (deterministic or LangChain), and
   normalizes the response with fallback.
6. **Governance** — the response is authorized, PII-masked, and audited.
7. **Streaming** — tokens stream back over SSE with a terminal `done` frame.

---

## 8. Domain Modules Deep Dive

| Module | Responsibility |
|---|---|
| `observability` | Correlation context (tenant/correlation/session id ContextVars), JSON log formatter, latency breakdown recorder, Langfuse tracing seam. |
| `security` | `SecurityContextValidator` — ingress validation over the shared `SecurityContext` contract; enforced before any execution. |
| `conversation` | Conversation Digital Twin (7 lifecycle states), optimistic-concurrency store, lifecycle transitions, lifecycle events. |
| `session` | Session model + store with TTL/expiry and optimistic concurrency. |
| `intent` | Deterministic intent classifier + `IntentGate` (routes personal→memory, organizational→knowledge; clarifies below confidence threshold). |
| `context` | `ContextAssembler` → ranked, token-bounded `ExecutionContextPackage` with citation-readiness filtering and lineage/metrics. |
| `prompt` | `PromptOrchestrator` — declarative layered templates, safe variable substitution, citation-readiness validation. |
| `integrations` | `build_chat_model` LangChain seam (huggingface/ollama), lazily imported. |
| `gateway` | Model registry/selector, deterministic + LangChain providers, `LLMGateway` single boundary, token/cost governance + budget ledger. |
| `memory` | 6-tier `MemoryFramework` (remember/recall/consolidate/forget/expire), confidence-by-validation-method, per-scope TTL. |
| `tools` | Tool ABC + `PermissionGate` + `ToolExecutor` (tools never called directly). |
| `agents` | Capability-based `AgentSelector` + bounded runtime (sequential + LangGraph) + `AgentCoordinator`. |
| `planning` | Rule-based `PlanningEngine` producing an ordered task DAG with approval gates. |
| `governance` | RBAC + ABAC `PolicyEngine`, `GovernanceGuard` PEP, immutable audit trail, PII masking, secret redaction, security-context propagation. |
| `knowledge` | EKRE HTTP client behind a circuit breaker with 429 backpressure handling and graceful degradation. |
| `workflow` | `WorkflowOrchestrator` (objective → plan → lifecycle) + platform event bus. |
| `readiness` | Deployment, multi-tenancy, and master handoff readiness assessments. |

Domain modules never import configuration directly. The composition root
(`composition.py`) reads settings and injects dependencies via `build_*`
factories.

---

## 9. Security, Governance & Compliance

- **Gateway authentication (trust boundary).** EKCP performs no end-user
  authentication of its own; it trusts an upstream gateway to authenticate the
  user and set identity, roles, and clearance. When
  `EKCP_SECURITY__REQUIRE_GATEWAY_AUTH=true`, every governed route requires the
  shared token (`Authorization: Bearer` or `X-Service-Token`) and fails closed if
  the token is unconfigured. Health and readiness probes stay open.
- **Least-privilege roles.** The default role is `user`. With
  `TRUST_REQUEST_ROLES=false`, request-body roles are ignored and every caller is
  pinned to the default role, preventing self-elevation; leave it `true` only when
  the gateway supplies roles from a verified token.
- **Admission control.** Per-tenant concurrency is enforced at request time
  (`EKCP_DEPLOYMENT__TENANT_MAX_CONCURRENT`); an over-limit tenant receives `429`.
  Ingress text inputs are length-bounded to bound resource use.
- **Security ingress.** Every governed request must carry a security context whose
  `tenant_id` matches `X-Tenant-ID`; the validator rejects missing, mismatched, or
  unknown-clearance contexts with `403`.
- **Authorization.** A combined RBAC + ABAC `PolicyEngine` checks role permissions
  (`ROLE_PERMISSIONS`) and classification clearance before agent, memory, and
  model operations. `GovernanceGuard` is the policy-enforcement point — governance
  is a prerequisite, not an afterthought.
- **Audit.** Every governed decision produces an immutable `AuditRecord`. Sinks:
  `memory` (queryable via `/governance/audit`, ephemeral), `file` (durable
  append-only JSONL that survives restarts, for compliance evidence), or
  `logging` (streams to logs).
- **PII masking.** Outbound model and agent responses are masked (email, phone,
  SSN, credit card) before leaving the service. With `MASK_INBOUND=true`, inbound
  content (e.g. memory writes) is also scrubbed of PII before it is persisted.
- **Secret redaction.** A logging filter scrubs registered secret values and
  sensitive field names from all application and server log records; installed
  automatically at startup.
- **Classification propagation.** Security context propagated to EKRE is monotonic
  — classification never downgrades (unless explicitly allowed).

---

## 10. Memory Framework

Six tiers with distinct retention: **working** (30 min), **session** (8 h),
**conversation** (30 d), **workspace** (1 y), **user** (3 y), and
**organizational** (indefinite). Operations:

- **remember** — store with confidence derived from the validation method
  (user-confirmed > tool-verified > knowledge-retrieved > agent-generated >
  llm-inferred) and a per-scope expiry.
- **recall** — multi-dimensional ranking (relevance, recency, importance,
  frequency, trust) feeding the context assembler.
- **consolidate** — summarize/abstract a conversation's active memories into a
  long-term memory, archiving the sources.
- **forget** — hard-delete for a user or conversation (right-to-be-forgotten).
- **expire** — mark past-TTL memories expired.

Memory is wired into `/context/build` via `include_memory` and is the graceful
fallback when EKRE knowledge degrades.

---

## 11. Observability & Tracing

- **Correlation context.** Tenant, correlation, and session ids are bound per
  request as ContextVars and injected into every log record.
- **Structured logging.** A JSON formatter emits machine-parseable records
  carrying `tenant_id` and `correlation_id`.
- **Latency.** A latency recorder captures per-stage timings and flags budget
  overruns against the first-response NFR.
- **Tracing.** A Langfuse callback seam is lazily wired when
  `EKCP_OBSERVABILITY__LANGFUSE_ENABLED=true` (self-hosted only).

---

## 12. Resilience & Knowledge Integration

When `EKCP_KNOWLEDGE__ENABLED=true`, EKCP retrieves enterprise knowledge from EKRE
over HTTP, protected by a **circuit breaker** (default 5 failures → open, 60 s →
half-open). The client handles `429` backpressure and timeouts. On any failure the
breaker records it and retrieval **degrades gracefully** to local memory — the
conversation never fails because knowledge is unavailable. The `/context/build`
response surfaces `degraded: true` with a warning, and a `CONTEXT_DEGRADED`
platform event is published.

---

## 13. NFR Validation & Readiness

EKCP exposes code-level readiness assessments (a report is `ready` when it has no
`error` findings; `warning` findings are advisory):

- **Deployment** (`GET /v1/readiness`) — plane separation, HA replicas, circuit
  breaker, tenant admission ceiling, first-response latency, and availability NFR.
- **Multi-tenancy** (`GET /v1/readiness/tenancy`) — tenant boundary, per-tenant
  admission ceiling, and tenant-aware observability.
- **Master handoff** (`GET /v1/readiness/handoff`) — the KPI gates: conversation
  completion, first-response latency (advisory), tool and agent success,
  conversation recovery, and 100 % policy/audit coverage.

Targets are configuration-driven (`EKCP_DEPLOYMENT__*`). Container/cluster
orchestration is out of scope — these gates validate the configuration a real
deployment must satisfy.

---

## 14. The Master Integration Handoff

`GET /v1/readiness/handoff` returns the immutable `MasterHandoffPackage` that
Product, Architecture, and Quality sign off for master integration:

- **Endpoints** — the 16 HTTP endpoints EKCP exposes.
- **Contracts** — the cross-service contracts EKCP consumes/produces:
  `SecurityContext`, `RetrievalContextPackage`, `RetrievalCandidate`, `Citation`.
- **KPIs** — the proven conversation, tool, agent, recovery, and coverage metrics.
- **Coverage** — policy-enforcement and audit coverage (1.0).
- **Report** — the readiness report backing the `ready` flag.

EKCP is the response-generation endpoint of the platform: EKIE ingests, EKRE
retrieves, and EKCP converses — consuming EKRE's `RetrievalContextPackage` and
returning grounded, governed responses.

---

## 15. LangChain / LangGraph Integration

LangChain and LangGraph live behind engine-owned seams and are never imported on
the offline path:

- **Chat model.** `domain/integrations/build_chat_model` constructs a HuggingFace
  or Ollama chat model, used by the `LangChainChatProvider` behind the gateway.
  Selected via `EKCP_MODEL__RUNTIME=langchain`.
- **Agent runtime.** `EKCP_AGENT__RUNNER=langgraph` routes agent execution through
  a LangGraph graph with an in-memory checkpointer and a conditional fallback
  edge. The default `sequential` runner is deterministic and dependency-free.

Install the `[huggingface]` or `[orchestration]` extras to enable these paths.

---

## 16. Demo Scripts

Each script runs fully offline and demonstrates one sprint's capability. Run from
the repository root:

```powershell
.\.venv\Scripts\python.exe services/ekcp/scripts/demo_foundations.py
```

| Script | Demonstrates |
|---|---|
| `demo_foundations.py` | Security gate, latency breakdown, SSE echo schema. |
| `demo_conversation.py` | Conversation lifecycle + intent routing + clarification. |
| `demo_context_prompt.py` | Context assembly + layered prompt with citations. |
| `demo_model_gateway.py` | Governed model invocation, streaming, budget ledger. |
| `demo_memory.py` | Memory recall ranking, routing, consolidation, forget. |
| `demo_agents.py` | Planning, agent execution with tools, coordination + approval. |
| `demo_governance.py` | RBAC/ABAC allow/deny, PII masking, audit trail. |
| `demo_workflow.py` | Workflow trigger + events; knowledge degradation. |
| `demo_readiness.py` | Deployment/tenancy readiness + master handoff package. |

---

## 17. Testing

The green gate must be clean before any change is accepted:

```powershell
# Lint.
.\.venv\Scripts\python.exe -m ruff check services/ekcp

# Type-check (strict).
Push-Location services/ekcp; ..\..\.venv\Scripts\python.exe -m mypy src; Pop-Location

# Test.
Push-Location services/ekcp; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location
```

Current status: **172 tests passing**, ruff clean, mypy `--strict` clean on 133
source files. Tests are hermetic — they construct settings with `_env_file=None`
so they never read a developer `.env`.

---

## 18. Troubleshooting

| Symptom | Cause | Resolution |
|---|---|---|
| `401 Unauthorized` on a governed route | Gateway auth enabled; missing/invalid token. | Send `Authorization: Bearer <token>` or `X-Service-Token` matching `EKCP_SECURITY__GATEWAY_AUTH_TOKEN`. |
| `503` "gateway authentication ... not configured" | Auth required but `GATEWAY_AUTH_TOKEN` blank. | Set a token, or disable `REQUIRE_GATEWAY_AUTH`. |
| `429 Too Many Requests` | Tenant exceeded `TENANT_MAX_CONCURRENT`. | Retry after a moment or raise the ceiling. |
| `403 Forbidden` on a governed route | Missing/mismatched security context or `X-Tenant-ID`. | Send `X-Tenant-ID` and a `security_context` whose `tenant_id` matches. |
| `400 Bad Request` "tenant" | Missing `X-Tenant-ID` header. | Add the header. |
| `403` on `/agent/execute` or `/memory/*` | Role lacks the required permission. | Use a role/permission that grants `INVOKE_AGENT` / `READ_MEMORY` / `WRITE_MEMORY`. |
| `409 Conflict` on conversation/workflow | Invalid state transition or version conflict. | Reload current state; retry the valid action. |
| `413` on `/model/invoke` | Prompt exceeds the token limit. | Reduce context or raise `EKCP_MODEL__MAX_TOKENS_PER_REQUEST` / `CONTEXT_WINDOW`. |
| `/context/build` returns `degraded: true` | EKRE unavailable; fell back to memory. | Verify EKRE is running at `EKCP_KNOWLEDGE__BASE_URL`; check the circuit breaker. |
| `ModuleNotFoundError` for `langchain_*` / `langgraph` | Live runtime selected without the extra installed. | Install `[huggingface]` or `[orchestration]`, or revert to the deterministic/sequential default. |
| Settings not picked up | `.env` not found or wrong prefix. | Place `.env` in `services/ekcp/`; use the `EKCP_` prefix and `__` delimiter. |

---

## 19. Glossary

| Term | Meaning |
|---|---|
| **Conversation Digital Twin** | The stateful model of a conversation and its lifecycle. |
| **Intent Gate** | Deterministic classifier that resolves intent and routes (or clarifies) before execution. |
| **Execution Context Package** | The ranked, token-bounded, governed context assembled for a turn. |
| **Prompt Package** | The validated prompt constructed from declarative layered templates. |
| **LLM Gateway** | The single governed boundary for every model call. |
| **Memory tier** | One of working/session/conversation/workspace/user/organizational scopes. |
| **GovernanceGuard** | The policy-enforcement point wiring authorization, audit, and masking. |
| **Circuit breaker** | Resilience component that trips on repeated EKRE failures and recovers via half-open probing. |
| **MasterHandoffPackage** | The immutable readiness artifact signed off for master integration. |
| **Readiness finding** | An info/warning/error check outcome; a report is `ready` when it has no errors. |

---

For architecture rationale see [EKCP-handbook.md](EKCP-handbook.md); for setup and
configuration see [EKCP-Deployment-Guide.md](EKCP-Deployment-Guide.md); for sprint
history and acceptance evidence see
[../sprints/ekcp-sprint-track.md](../sprints/ekcp-sprint-track.md).

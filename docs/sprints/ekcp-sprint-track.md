# EKCP Sprint Track

> Track Owner: EKCP Engine Lead
> Start Condition: EKRE sprint exit gate passed
> Objective: Deliver EKCP as a governed conversational orchestration platform that turns user intent into trusted, explainable, policy-compliant responses using conversation, context, memory, agents, tools, and a model-agnostic LLM gateway.
> Source Of Truth: [../EKCP/EKCP-handbook.md](../EKCP/EKCP-handbook.md)

## Alignment To Handbook
This track is decomposed directly from the EKCP Enterprise Architecture Handbook and its MVP Build Plan (Chapter 23). It honors the handbook design philosophy: conversation first, intent before execution, context before generation, model independence, governance and auditability by default. Delivery follows the layered MVP approach: build a thin end-to-end vertical slice first, then expand intelligence iteratively.

Build order: Foundations and Gateway, Conversation Core Loop, Context and Prompt Orchestration, Model Gateway, Memory, Agent Runtime and Tools, Governance and Security, Workflow and Knowledge integration, then Deployment and master handoff readiness.

## Reference Implementation And Model Strategy
This track uses LangChain and LangGraph as the reference orchestration stack, kept behind engine-owned abstractions to preserve model independence (see [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md)).

Where LangChain and LangGraph are used:
1. Prompt Orchestration (EKCP-S2): prompts are constructed with ChatPromptTemplate using explicit input variables and partial variables for format instructions; no hardcoded prompt strings.
2. Model Gateway (EKCP-S3): a `build_chat_model(settings)` factory returns a LangChain chat model behind the engine-owned gateway seam, using LCEL (prompt | model | parser), PydanticOutputParser or StrOutputParser, and streaming for user-facing responses. The gateway stays model-agnostic; the model is configuration-selected.
3. Agent Runtime and Planning (EKCP-S5): LangGraph drives agent coordination and planning, using typed graph state, tools as pure-function nodes with permission checks, conditional edges for fallback, and a checkpointer for conversation recovery.

Model runtime: Ollama (self-hosted, local-first) is the default chat provider (for example llama3.1), selected through the model gateway. No enterprise data leaves the local environment by default. All model names, hosts, and parameters are configuration-driven.

Observability and governance: every LLM and agent invocation carries tenant_id, correlation_id, and session_id, is traced via the self-hosted Langfuse callback, and passes policy checks before execution. Model independence is preserved so no provider is hardcoded into engine logic.

## Track Definition Of Ready
1. EKRE sprint exit gate is approved; retrieval response and citation contracts are versioned in packages/contracts.
2. Security context contract is consumable by EKCP for downstream retrieval requests.
3. EKCP story owners, reviewers, and quality owners are assigned.
4. Model gateway provider and policy and audit baseline expectations are approved.

## Track Definition Of Done
1. All sprint stories meet acceptance criteria with review evidence.
2. Intent is validated before execution and context is assembled before generation on all governed paths.
3. Policy checks are enforced and audit evidence is complete for governed execution paths.
4. Responses only ship with valid citation compliance; conversation recovery works after interruption.
5. Master integration handoff package is approved by Product, Architecture, and Quality.

## Success Metrics (Track Level, From Handbook KPIs)
1. Successful conversation completion >= 99%.
2. Average first response latency <= 3 seconds excluding long-running tools.
3. Tool execution success rate >= 99%; agent orchestration success rate >= 99%.
4. Conversation recovery success: 100%.
5. Policy enforcement coverage and conversation audit coverage: 100%.

## EKCP-S0: Platform Foundations And API Gateway
Handbook mapping: Chapter 3 (Conversation Architecture), Chapter 18 (Deployment planes), Chapter 19 (Microservices decomposition), Chapter 20 (API Contracts), Chapter 12 (Governance baseline).

> Status: Approved (15 pytest green, ruff + mypy --strict clean on 18 source files). Implemented in `services/ekcp/` mirroring EKIE and EKRE conventions: `config/settings.py` (`EKCP_*` env-driven), `domain/observability` (correlation context with tenant/correlation/session ids, structured JSON logging, latency breakdown, Langfuse tracing seam), `domain/security` (security context ingress validator over the shared `SecurityContext` contract), `api/` (single-entry FastAPI app with correlation middleware, CORS, health probes, and the SSE `POST /chat/stream` contract), and `composition.py`.

### Sprint Objective
Establish the control, runtime, and data plane substrate with a single API gateway, auth, routing, and observability baseline.

### Scope
1. API gateway with authentication and routing.
2. Service decomposition and API contract baseline.
3. Observability baseline (request tracing, latency, token usage) with tenant_id and correlation_id.
4. Governance and configuration baseline.

### Out Of Scope
1. Agent runtime and tool execution.
2. Advanced governance engine.

### Stories
1. EKCP-S0-1 API gateway, auth, and routing.
2. EKCP-S0-2 Service decomposition and API contract baseline.
3. EKCP-S0-3 Observability baseline (tracing, latency, token usage).
4. EKCP-S0-4 Governance and configuration baseline.
5. EKCP-S0-5 SSE streaming chat API contract for web UI consumption: define endpoint (`POST /chat/stream`), SSE event schema (`token`, `citation`, `done`, `error`), tenant and correlation header convention, and error event format. This contract is the start condition for the Web UI sprint track (UI-S0).

### Delivery Evidence
1. EKCP-S0-1 Approved: `api/app.py` exposes a single FastAPI entry point with `CorrelationMiddleware` binding `X-Tenant-ID`, `X-Correlation-ID`, and `X-Session-ID`; configuration-driven CORS; and `api/dependencies.py` enforcing the tenant header (400 when absent).
2. EKCP-S0-2 Approved: router-per-feature decomposition (`api/health.py`, `api/chat.py`) with typed Pydantic request and response models; the app factory wires routers from `create_app(settings)`.
3. EKCP-S0-3 Approved: `domain/observability/` binds tenant/correlation/session ids to structured JSON logs and records a per-stage `LatencyBreakdown` with budget-breach detection; the Langfuse tracing seam stays off on the offline path.
4. EKCP-S0-4 Approved: `config/settings.py` (`EKCP_*` env-driven, local-first defaults) plus `domain/security` validate the security context on every governed request; no operational values are hardcoded.
5. EKCP-S0-5 Approved: `api/chat.py` defines `POST /chat/stream` and the `token`/`citation`/`done`/`error` SSE event schema, enforces the security context gate (403), and streams an echo stub so the Web UI can integrate against a stable contract ahead of model-backed generation.

### Deliverables
1. API gateway and routing design.
2. Service and API contract baseline.
3. Observability and configuration baseline.
4. SSE streaming chat API contract document consumed by the Web UI sprint track.

### Acceptance
1. Single entry point enforces auth and routing.
2. No hardcoded operational values; configuration-driven behavior.
3. Every request exposes trace and latency data.
4. SSE streaming chat API contract is approved and referenced by the Web UI sprint track.

### Exit Evidence
1. Approved gateway and API contract baseline.
2. Observability baseline evidence.
3. Approved SSE streaming chat API contract (EKCP-S0-5).

## EKCP-S1: Conversation Core Loop
Handbook mapping: Chapter 4 (Conversation Engine), Chapter 5 (Session and State Management).

> Status: Approved (42 pytest green, ruff + mypy --strict clean on 38 source files). Implemented in `services/ekcp/src/domain/{conversation,session,intent}` with the Conversation Digital Twin lifecycle state machine, optimistic-concurrency stores, session management, and the deterministic intent-before-execution gate, surfaced through `POST /conversation/start` and `POST /conversation/message`.

### Sprint Objective
Deliver the conversation core with a persistent Conversation Digital Twin, session state, and intent gating before execution.

### Scope
1. Conversation lifecycle and Conversation Digital Twin.
2. Session and state management.
3. Intent gating (intent before execution).

### Out Of Scope
1. Memory, agents, and tools.

### Stories
1. EKCP-S1-1 Conversation lifecycle and CDT model.
2. EKCP-S1-2 Session and state management.
3. EKCP-S1-3 Intent gating and confidence policy.

### Delivery Evidence
1. EKCP-S1-1 Approved: `domain/conversation/` defines the immutable `ConversationDigitalTwin`, the seven-state lifecycle machine (`lifecycle.py` legal-transition table + validated `transition()` with history and version bump), an optimistic-concurrency `ConversationStore` (in-memory default), the `ConversationManager` administration interface, the `ConversationEngine` core interaction loop, and the event dispatcher.
2. EKCP-S1-2 Approved: `domain/session/` provides the immutable `Session` model, an optimistic-concurrency `SessionStore` (in-memory default), and a `SessionManager` enforcing the expiration policy; sessions are independent of conversations and expiration never terminates a conversation.
3. EKCP-S1-3 Approved: `domain/intent/` provides a deterministic `IntentClassifier` and `IntentGate` that classify intent, scope (personal versus organizational), and confidence, request clarification below the configured threshold, and route personal messages to memory and organizational messages to enterprise knowledge (EKRE) — execution never proceeds from ungated raw input.

### Deliverables
1. Conversation lifecycle and CDT artifact.
2. Session and state model.
3. Intent gating policy.

### Acceptance
1. Conversation lifecycle and transitions are fully defined.
2. Execution never occurs directly from raw user input.
3. Conversation state persists and recovers after interruption.

### Exit Evidence
1. Approved conversation lifecycle specification.
2. Intent gating policy sign-off.

## EKCP-S2: Context And Prompt Orchestration
Handbook mapping: Chapter 6 (Context Orchestration), Chapter 7 (Prompt Orchestration), plus prompting standards in [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md).

> Status: Approved (60 pytest green, ruff + mypy --strict clean on 54 source files). Implemented in `services/ekcp/src/domain/{context,prompt}`: the `ContextAssembler` builds a governed, ranked, token-bounded Execution Context Package; the `PromptOrchestrator` constructs prompts from declarative layered templates with explicit named variables (no hardcoded prompt strings); and citation-readiness validation strips retrieval candidates with incomplete citations before prompt generation. Surfaced through `POST /context/build` and `POST /prompt/generate`.

### Sprint Objective
Assemble intentional context before generation and construct governed prompts with ChatPromptTemplate, consuming EKRE retrieval context.

### Scope
1. Context orchestration from conversation history and EKRE retrieval.
2. Prompt orchestration and dynamic prompt construction using ChatPromptTemplate with explicit input variables and no hardcoded prompt strings.
3. Citation-readiness validation of incoming retrieval context.

### Out Of Scope
1. Model provider integration (next sprint).

### Stories
1. EKCP-S2-1 Context assembly and source prioritization.
2. EKCP-S2-2 Prompt orchestration and construction.
3. EKCP-S2-3 Retrieval context citation-readiness validation.

### Delivery Evidence
1. EKCP-S2-1 Approved: `domain/context/` assembles the immutable `ExecutionContextPackage` from conversation history, enterprise knowledge (EKRE `RetrievalContextPackage`), memory, tool, and policy sources; ranks by relevance and recency, deduplicates, filters below-threshold items, and enforces a token budget with graceful degradation (policy items always retained). Every included item carries lineage (source, reason, rank, policy status) so assembled context is auditable before generation.
2. EKCP-S2-2 Approved: `domain/prompt/` constructs prompts from a declarative layered template registry (system, policy, conversation, task, formatting) with explicit named variables resolved from the context package; no prompt strings are hardcoded in engine logic, the assistant identity and behavior are configuration-driven, and construction is validated (required variables present, token budget honored) into an immutable `PromptPackage`.
3. EKCP-S2-3 Approved: `domain/prompt/citations.py` validates incoming retrieval context and strips any candidate missing `source_path`, `document_id`, `chunk_id`, or content before prompt generation, preventing hallucinated citations; the assembler applies the same rule and reports dropped items.

### Deliverables
1. Context orchestration decision policy.
2. Prompt construction policy.
3. Citation-readiness validation checklist.

### Acceptance
1. Context is assembled before generation and is auditable.
2. Prompts are constructed dynamically, not hardcoded.
3. Incoming citations are validated before use.

### Exit Evidence
1. Approved context and prompt orchestration policies.
2. Citation-readiness validation evidence.

## EKCP-S3: Model Management And LLM Gateway
Handbook mapping: Chapter 14 (Enterprise Model Management and LLM Gateway), plus chat model and LCEL standards in [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md).

> Status: Approved (80 pytest green, ruff + mypy --strict clean on 66 source files). Implemented in `services/ekcp/src/domain/{gateway,integrations}`: a model-agnostic `LLMGateway` is the single boundary for all model calls, with a `build_chat_model` factory (deterministic offline default, HuggingFace/Ollama config-selected via LCEL), a model registry and deterministic selector, automatic fallback, response normalization, streaming, and mandatory token and cost governance. Surfaced through `POST /model/invoke` and the gateway-backed SSE `POST /chat/stream`.

### Sprint Objective
Deliver a model-agnostic LLM gateway with a `build_chat_model(settings)` factory (Ollama default), LCEL response generation, streaming, and token governance.

### Scope
1. Model gateway abstraction and provider adapter, exposing a `build_chat_model(settings)` factory that returns a LangChain chat model behind the engine seam.
2. Response generation and multiple response types using LCEL (prompt | model | parser) with streaming for user-facing responses.
3. Token usage governance and cost tracking.

### Out Of Scope
1. Multi-model routing optimization.

### Stories
1. EKCP-S3-1 Model gateway abstraction and provider adapter.
2. EKCP-S3-2 Response generation and response types.
3. EKCP-S3-3 Token usage and cost governance.

### Delivery Evidence
1. EKCP-S3-1 Approved: `domain/integrations/langchain_resources.py` exposes the provider-abstracted `build_chat_model` factory (HuggingFace or Ollama, lazily imported), and `domain/gateway/` provides the `ChatModelProvider` ABC with a `DeterministicEchoProvider` (local-first offline default) and a lazy `LangChainChatProvider`, plus a `ModelRegistry` (lifecycle-gated so only approved models serve) and a deterministic `ModelSelector`. No platform component calls a provider directly; all invocations pass through the gateway.
2. EKCP-S3-2 Approved: the `LLMGateway` normalizes every response into the Model Invocation Contract output, generates via LCEL (prompt | model | parser) with configurable response types, supports token streaming, and applies automatic fallback across the candidate chain; the SSE `POST /chat/stream` endpoint streams gateway tokens and a terminal done frame with usage.
3. EKCP-S3-3 Approved: `domain/gateway/governance.py` enforces mandatory token accounting on every invocation, per-request token and cost ceilings (token-limit and budget guards), and a per-tenant budget ledger; the normalized response carries token usage and a cost estimate.

### Deliverables
1. Model gateway contract.
2. Response generation policy.
3. Token and cost governance artifact.

### Acceptance
1. EKCP remains model-independent behind the gateway.
2. First response latency target <= 3 seconds is demonstrable.
3. Token usage is tracked and governed.

### Exit Evidence
1. Approved model gateway contract.
2. Latency and token governance evidence.

## EKCP-S4: Memory Framework
Handbook mapping: Chapter 8 (Memory Framework).

> Status: Approved (96 pytest green, ruff + mypy --strict clean on 78 source files). Implemented in `services/ekcp/src/domain/memory`: a tiered `MemoryFramework` (working, session, conversation, workspace, user, organizational) with confidence-by-validation-method, deterministic multi-dimensional retrieval that feeds the S2 context assembler, summary and abstract consolidation, per-scope retention with expiry, and right-to-be-forgotten purge. Surfaced through `POST /memory/{store,retrieve,consolidate,purge}` and the `include_memory` option on `POST /context/build`.

### Sprint Objective
Deliver governed conversation and long-term memory with retention controls.

### Scope
1. Active conversation memory and long-term memory.
2. Memory retrieval and context compression.
3. Memory retention, expiration, and governance.

### Out Of Scope
1. Agent and tool execution.

### Stories
1. EKCP-S4-1 Conversation and long-term memory model.
2. EKCP-S4-2 Memory retrieval and compression.
3. EKCP-S4-3 Memory retention and governance policy.

### Delivery Evidence
1. EKCP-S4-1 Approved: `domain/memory/models.py` defines the immutable, scoped `MemoryItem` across the six memory tiers with type, topic, lineage, and a confidence derived from the validation method (`confidence.py`), persisted through a `MemoryStore` (in-memory offline default); active conversation memory and long-term memory are distinguished by scope and consolidation.
2. EKCP-S4-2 Approved: `domain/memory/retrieval.py` ranks memories by a weighted blend of relevance, recency, importance, frequency, and trust and exposes them as `ContextItem` objects consumed by the S2 assembler (`include_memory`), and `compression.py` consolidates a conversation's memories into a long-term summary or abstract while archiving the sources.
3. EKCP-S4-3 Approved: `domain/memory/retention.py` applies per-scope TTLs, expires aged memories, and hard-deletes memories for a user or conversation (right-to-be-forgotten), while `routing.py` reuses the S1 intent scope to route personal queries to memory and organizational queries to enterprise knowledge (EKRE).

### Deliverables
1. Memory model and lifecycle artifact.
2. Memory retrieval policy.
3. Memory governance policy.

### Acceptance
1. Memory controls align with compliance requirements.
2. Personal versus organizational routing is defined (memory versus EKRE).

### Exit Evidence
1. Approved memory model and governance policy.

## EKCP-S5: Agent Runtime, Tools And Planning
Handbook mapping: Chapter 9 (Agent Runtime), Chapter 10 (Tool Execution), Chapter 11 (Planning and Orchestration), plus LangGraph standards in [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md).

> Status: Approved (120 pytest green, ruff + mypy --strict clean on 99 source files). Implemented in `services/ekcp/src/domain/{tools,agents,planning}`: permission-gated tool execution (tools never called directly), capability-based agent selection and a bounded agent runtime (Sequential offline default plus a lazy LangGraph runner with a checkpointer and a conditional fallback edge), a rule-based planning engine producing an ordered task DAG with human approval gates, and a coordinator that halts at approval. Surfaced through `POST /agent/execute` and `POST /agent/plan`.

### Sprint Objective
Deliver governed agent coordination, tool execution with permission checks, and planning orchestration on a LangGraph runtime.

### Scope
1. Agent runtime and coordination built on LangGraph with typed graph state and a checkpointer for conversation recovery.
2. Tool execution with permission validation and failure handling, with tools as pure-function nodes gated by policy.
3. Planning and orchestration engine using conditional edges for fallback paths.

### Out Of Scope
1. Full plugin system.

### Stories
1. EKCP-S5-1 Agent runtime and coordination.
2. EKCP-S5-2 Tool execution with permission validation.
3. EKCP-S5-3 Planning and orchestration engine.
4. EKCP-S5-4 Failure handling and fallback policy.

### Delivery Evidence
1. EKCP-S5-1 Approved: `domain/agents/` provides capability-based agent selection (never by name), a bounded agent runtime that runs an optional permitted tool step then a reasoning step via the model gateway, a `SequentialAgentRunner` offline default and a lazy `LangGraphAgentRunner` (typed graph state, `MemorySaver` checkpointer for recovery, conditional fallback edge), and an `AgentCoordinator` for multi-agent plans.
2. EKCP-S5-2 Approved: `domain/tools/` defines the `Tool` ABC (pure-function capabilities), an authoritative registry with capability discovery, a `PermissionGate` that authorizes before execution (unauthorized execution is blocked), and a `ToolExecutor` pipeline (validate, authorize, execute with bounded retries, normalize, audit) producing an auditable `ToolResult`.
3. EKCP-S5-3 Approved: `domain/planning/` decomposes an objective into an immutable `ExecutionPlan` of capability-scoped tasks with finish-to-start dependencies, deterministic topological ordering with cycle detection, and human approval checkpoints; the plan drives coordinated agent execution.
4. EKCP-S5-4 Approved: failure handling is predictable — tools retry then return a failed result, unauthorized or unknown tools degrade to failed results in the agent loop, agent generation failures return a failed outcome with recommended next actions, steps are bounded to prevent runaway loops, and the LangGraph runner adds a conditional fallback path.

### Deliverables
1. Agent orchestration policy.
2. Tool governance and permission matrix.
3. Planning and fallback policy.

### Acceptance
1. Unauthorized tool execution is blocked by policy.
2. Tool execution success target >= 99% and agent orchestration success target >= 99% are demonstrable.
3. Failure handling is predictable and documented.

### Exit Evidence
1. Approved agent and tool governance policies.
2. Failure-path scenario evidence.

## EKCP-S6: Governance, Security And Policy
Handbook mapping: Chapter 12 (Governance, Security and Policy Framework).

> Status: Approved (137 pytest green, ruff + mypy --strict clean on 111 source files). Implemented in `services/ekcp/src/domain/governance`: an RBAC + ABAC `PolicyEngine` and a `GovernanceGuard` policy-enforcement point wired into the agent, memory, and model endpoints (governance as prerequisite), an immutable append-only audit trail, PII masking of outbound responses, secret log redaction, and security-context propagation to EKRE with monotonic classification. Surfaced through `POST /governance/evaluate` and `GET /governance/audit`.

### Sprint Objective
Enforce policy across execution and produce complete audit trails.

### Scope
1. Policy enforcement on tool execution and data access.
2. Complete audit trails for compliance.
3. Security context propagation to EKRE.

### Out Of Scope
1. Master integration execution.

### Stories
1. EKCP-S6-1 Policy enforcement engine.
2. EKCP-S6-2 Audit trail completeness.
3. EKCP-S6-3 Security context propagation to EKRE.

### Delivery Evidence
1. EKCP-S6-1 Approved: `domain/governance/` provides RBAC roles and permissions (`ROLE_PERMISSIONS`), ABAC clearance ranking with no-downgrade enforcement, and a `PolicyEngine` (`evaluate`/`authorize`) surfaced through a `GovernanceGuard` policy-enforcement point that authorizes governed operations before they run; the guard is wired into `/agent/execute` (invoke_agent), `/memory/*` (read/write_memory), and `/model/invoke` (generate_response), and unauthorized operations are blocked with a 403.
2. EKCP-S6-2 Approved: every governed decision is recorded to an immutable, append-only `AuditSink` (in-memory and logging) with a complete `AuditRecord` (actor, action, result, resource, tenant, correlation, policy version, reason); `GET /governance/audit` returns the trail, PII is masked from outbound responses, and secret values are redacted from all logs via the installed `RedactionFilter`.
3. EKCP-S6-3 Approved: `domain/governance/propagation.py` packages the validated principal into the shared `SecurityContext` payload (`user_id`, `tenant_id`, `classification_clearance`) injected on downstream EKRE requests, enforcing monotonic classification so a propagated context can never weaken the caller's clearance; propagation is audited (consumed by EKCP-S7).

### Deliverables
1. Policy enforcement matrix.
2. Audit evidence completeness package.
3. Security context propagation design.

### Acceptance
1. Policy enforcement coverage: 100% on governed paths.
2. Audit trace coverage: 100% for governed scenarios.
3. Security context is injected on every EKRE request.

### Exit Evidence
1. Policy and audit evidence.
2. Security context propagation sign-off.

## EKCP-S7: Workflow, Events And Knowledge Integration
Handbook mapping: Chapter 15 (Workflow and Event Orchestration), Chapter 16 (Enterprise Knowledge Platform integration).

> Status: Approved (154 pytest green, ruff + mypy --strict clean on 127 source files). Implemented in `services/ekcp/src/domain/{workflow,knowledge}`: a workflow orchestrator that decomposes an objective into a plan and advances it through its lifecycle while publishing platform events, and a resilient EKRE knowledge retriever behind a circuit breaker that handles 429 backpressure and timeouts and degrades gracefully to local memory without failing the session. Surfaced through `POST /workflow/{trigger,pause,resume,approve}`, `GET /workflow/{id}`, and the `include_knowledge` option on `POST /context/build`.

### Sprint Objective
Integrate workflow and event orchestration and validate EKRE knowledge consumption with graceful degradation.

### Scope
1. Workflow and event orchestration baseline.
2. EKRE consumption and cascading failure prevention (backpressure, circuit breaking).
3. Graceful degradation to local memory when EKRE is constrained.

### Out Of Scope
1. Full distributed workflow engine.

### Stories
1. EKCP-S7-1 Workflow and event orchestration baseline.
2. EKCP-S7-2 EKRE consumption with circuit breaking and backpressure handling.
3. EKCP-S7-3 Graceful degradation strategy.

### Delivery Evidence
1. EKCP-S7-1 Approved: `domain/workflow/` provides the immutable `Workflow` with a lifecycle state machine, an in-memory store, a standard `PlatformEvent` schema with an append-only `EventBus`, and a `WorkflowOrchestrator` that triggers a workflow by decomposing the objective into an execution plan (reusing the S5 planning engine) and publishes workflow and knowledge platform events; `POST /workflow/{trigger,pause,resume,approve}` and `GET /workflow/{id}` expose the lifecycle.
2. EKCP-S7-2 Approved: `domain/knowledge/` provides a `CircuitBreaker` (five-failure threshold, timed half-open probe) and a `KnowledgeRetriever` that calls the EKRE `/v1/query/retrieve` endpoint via a lazy HTTP client with the propagated security context, surfacing 429 as backpressure and timeouts as controlled failures that trip the breaker — preventing cascading failure; the EKRE base URL is configuration-driven and disabled by default for the offline path.
3. EKCP-S7-3 Approved: when EKRE is disabled, unavailable, rate-limited, or the circuit is open, the retriever returns a degraded `KnowledgeResult` and `POST /context/build` (`include_knowledge`) falls back to local memory and conversation history, emits a `CONTEXT_DEGRADED` platform event, and completes the request — the session never fails because enterprise knowledge is unavailable.

### Deliverables
1. Workflow and event orchestration artifact.
2. EKRE consumption resilience design.
3. Degradation and resilience readiness artifact.

### Acceptance
1. HTTP 429 backpressure from EKRE is handled with backoff and circuit breaking.
2. Degradation to local memory works without session failure.

### Exit Evidence
1. Resilience and degradation validation evidence.

## EKCP-S8: Deployment, Multi-Tenancy And Master Handoff Readiness
Handbook mapping: Chapter 18 (Deployment and Multi-Tenant), Chapter 19 (Microservices), Chapter 22 (Monorepo), Chapter 23 (MVP Build Plan and Readiness).

### Sprint Objective
Prove deployment, multi-tenant isolation, and readiness for master integration.

### Scope
1. Cloud-native deployment across control, runtime, and data planes.
2. Multi-tenant isolation and tenant-aware observability.
3. Response, audit, and degradation readiness validation.

### Out Of Scope
1. Master integration and release execution.

### Stories
1. EKCP-S8-1 Deployment across control, runtime, and data planes.
2. EKCP-S8-2 Multi-tenant isolation and tenant-aware observability.
3. EKCP-S8-3 Response, audit, and degradation readiness validation.
4. EKCP-S8-4 Master integration handoff readiness package.

### Deliverables
1. Deployment and multi-tenancy design with evidence.
2. Readiness validation package.
3. Master handoff package with policy and audit proof.

### Acceptance
1. Conversation completion, latency, and recovery KPIs are demonstrated.
2. Multi-tenant isolation is validated.
3. Policy and audit coverage remain at 100% on governed paths.

> Status: Approved (172 pytest green, ruff + mypy --strict clean on 133 source files). Implemented in `services/ekcp/src/domain/readiness`: a code-level readiness domain (`ReadinessReport` with a computed `ready` flag over severity-graded findings) that assesses deployment across the control, runtime, and data planes (high availability, resilience, admission control, and latency/availability NFR targets), multi-tenant isolation with a per-tenant concurrency limiter and tenant-aware observability, and the master integration handoff KPIs (conversation completion, first-response latency, tool and agent success, recovery, and policy/audit coverage) assembled into an immutable `MasterHandoffPackage` enumerating the exposed endpoints and consumed/produced contracts. Container and cluster orchestration are out of scope (local-first); the gates validate the configuration a real deployment must satisfy. Surfaced through `GET /v1/readiness`, `GET /v1/readiness/tenancy`, and `GET /v1/readiness/handoff`. This completes the EKCP track.

Delivery Evidence:
- EKCP-S8-1 Deployment readiness across planes: `domain/readiness/deployment.py` (`assess_deployment_readiness` checks replicas/HA, circuit-breaker resilience, tenant admission ceiling, first-response latency budget, and availability targets); `DeploymentSettings` (`EKCP_DEPLOYMENT__*`); `GET /v1/readiness`.
- EKCP-S8-2 Multi-tenant isolation and tenant-aware observability: `domain/readiness/tenancy.py` (`TenantConcurrencyLimiter` per-tenant admission control with a slot context manager; `assess_multi_tenant_isolation` validates tenant boundary, admission ceiling, and tenant-aware observability); `GET /v1/readiness/tenancy`.
- EKCP-S8-3 Response, audit, and degradation readiness: KPI gates in `domain/readiness/handoff.py` prove conversation completion, first-response latency (warning-only), tool and agent success, conversation recovery, and 100% policy/audit coverage against configured targets; graceful EKRE degradation retained from S7.
- EKCP-S8-4 Master integration handoff package: `build_master_handoff_package` assembles the immutable `MasterHandoffPackage` (service/version, 16 endpoints, 4 cross-service contracts, proven KPIs, policy/audit coverage, and the readiness report); `GET /v1/readiness/handoff`; offline `scripts/demo_readiness.py`.

EKCP TRACK COMPLETE (Phase 0 through EKCP-S8 approved).

### Exit Evidence
1. Signed deployment and readiness validation packages.
2. Product, Architecture, and Quality sign-off for master integration handoff.

## Risk Register (Track Level)
1. Risk: intent gating ambiguity causes inconsistent execution paths. Mitigation: freeze intent policy per sprint and require escalation rule approval (EKCP-S1).
2. Risk: context assembled after generation reduces answer trust. Mitigation: enforce context-before-generation in EKCP-S2.
3. Risk: incomplete audit capture blocks governance acceptance. Mitigation: enforce audit evidence checklist as hard exit artifact in EKCP-S6.
4. Risk: EKRE saturation cascades into chat failures. Mitigation: enforce circuit breaking and degradation in EKCP-S7.
5. Risk: model coupling reduces portability. Mitigation: enforce model-agnostic gateway in EKCP-S3.
6. Risk: LLM non-determinism or agent loops reduce reliability. Mitigation: validate structured outputs against Pydantic schemas, bound agent steps and tool permissions in LangGraph, and enforce policy and audit before every model or tool call (EKCP-S5, EKCP-S6).

## Reporting Cadence
1. Weekly sprint review with Product, Architecture, and Quality.
2. Mid-sprint dependency review focused on master handoff blockers.
3. End-sprint gate review with explicit go or hold decision.

## Sprint Board Backlog (Ready To Use)

### EKCP-S0 Foundations And Gateway
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S0-1 | API gateway, auth, and routing | High | EKCP Lead | T-Shirt M | EKRE gate | Approved gateway design |
| EKCP-S0-2 | Service decomposition and API contracts | High | API Contract Owner | T-Shirt M | EKCP-S0-1 | Approved API baseline |
| EKCP-S0-3 | Observability baseline | High | Observability Owner | T-Shirt S | EKCP-S0-1 | Tracing and latency baseline |
| EKCP-S0-4 | Governance and configuration baseline | Medium | Governance Owner | T-Shirt S | EKCP-S0-1 | Config baseline approved |

### EKCP-S1 Conversation Core Loop
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S1-1 | Conversation lifecycle and CDT | High | EKCP Lead | T-Shirt M | EKCP-S0 Exit | Approved lifecycle spec |
| EKCP-S1-2 | Session and state management | High | Platform Owner | T-Shirt M | EKCP-S1-1 | Approved state model |
| EKCP-S1-3 | Intent gating and confidence policy | High | Conversation PM | T-Shirt M | EKCP-S1-1 | Approved intent policy |

### EKCP-S2 Context And Prompt
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S2-1 | Context assembly and prioritization | High | Orchestration Owner | T-Shirt M | EKCP-S1 Exit | Approved context policy |
| EKCP-S2-2 | Prompt orchestration and construction | High | Prompt Owner | T-Shirt M | EKCP-S2-1 | Approved prompt policy |
| EKCP-S2-3 | Retrieval citation-readiness validation | High | Compliance Owner | T-Shirt S | EKCP-S2-1 | Citation-readiness checklist |

### EKCP-S3 Model Gateway
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S3-1 | Model gateway abstraction and adapter | High | Model Platform Owner | T-Shirt M | EKCP-S2 Exit | Approved gateway contract (build_chat_model) |
| EKCP-S3-2 | Response generation and types | High | Response Owner | T-Shirt M | EKCP-S3-1 | LCEL streaming response policy approved |
| EKCP-S3-3 | Token usage and cost governance | Medium | Governance Owner | T-Shirt S | EKCP-S3-1 | Token governance evidence |

### EKCP-S4 Memory
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S4-1 | Conversation and long-term memory | High | Memory Owner | T-Shirt M | EKCP-S3 Exit | Approved memory model |
| EKCP-S4-2 | Memory retrieval and compression | Medium | Memory Owner | T-Shirt M | EKCP-S4-1 | Retrieval policy approved |
| EKCP-S4-3 | Memory retention and governance | High | Governance Owner | T-Shirt S | EKCP-S4-1 | Governance policy approved |

### EKCP-S5 Agents, Tools And Planning
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S5-1 | Agent runtime and coordination | High | Agent Runtime Owner | T-Shirt M | EKCP-S4 Exit | Approved LangGraph orchestration policy |
| EKCP-S5-2 | Tool execution with permission checks | High | Security Owner | T-Shirt M | EKCP-S5-1 | Approved permission matrix |
| EKCP-S5-3 | Planning and orchestration engine | Medium | Planning Owner | T-Shirt M | EKCP-S5-1 | Approved LangGraph planning policy |
| EKCP-S5-4 | Failure handling and fallback | High | Reliability Owner | T-Shirt S | EKCP-S5-2 | Failure-path evidence |

### EKCP-S6 Governance And Security
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S6-1 | Policy enforcement engine | High | Governance Owner | T-Shirt M | EKCP-S5 Exit | Policy matrix approved |
| EKCP-S6-2 | Audit trail completeness | High | Quality Lead | T-Shirt M | EKCP-S6-1 | Signed audit evidence |
| EKCP-S6-3 | Security context propagation to EKRE | High | Security Owner | T-Shirt S | EKCP-S6-1 | Propagation sign-off |

### EKCP-S7 Workflow And Knowledge Integration
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S7-1 | Workflow and event orchestration baseline | Medium | Workflow Owner | T-Shirt M | EKCP-S6 Exit | Approved orchestration baseline |
| EKCP-S7-2 | EKRE consumption with circuit breaking | High | Reliability Owner | T-Shirt M | EKCP-S7-1 | Resilience evidence |
| EKCP-S7-3 | Graceful degradation strategy | High | Reliability Owner | T-Shirt S | EKCP-S7-2 | Degradation evidence |

### EKCP-S8 Deployment And Handoff
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKCP-S8-1 | Deployment across planes | High | DevOps Owner | T-Shirt M | EKCP-S7 Exit | Deployment evidence |
| EKCP-S8-2 | Multi-tenant isolation and observability | High | Platform Owner | T-Shirt M | EKCP-S8-1 | Isolation evidence |
| EKCP-S8-3 | Response, audit, and degradation readiness | High | Quality Lead | T-Shirt M | EKCP-S8-1 | Readiness pack |
| EKCP-S8-4 | Master integration handoff package | High | EKCP Lead | T-Shirt M | EKCP-S8-3 | Signed master handoff artifact |

## Track Dependencies
1. Must run after EKRE sprint exit gate.
2. Master integration cannot start until EKCP policy, audit, and readiness gate passes.

## Track Exit Gate
1. EKCP conversation, policy, audit, and deployment readiness gate approved by Product, Architecture, and Quality.

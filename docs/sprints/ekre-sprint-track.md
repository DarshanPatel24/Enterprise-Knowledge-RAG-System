# EKRE Sprint Track

> Track Owner: EKRE Engine Lead
> Start Condition: EKIE sprint exit gate passed
> Objective: Deliver EKRE as a secure, deterministic, explainable retrieval platform that transforms user queries into ranked, citation-preserving, policy-compliant context for EKCP.
> Source Of Truth: [../EKRE/EKRE-handbook.md](../EKRE/EKRE-handbook.md)

## Alignment To Handbook
This track is decomposed directly from the EKRE Enterprise Architecture Handbook domains. Each sprint maps to specific handbook chapters and enforces the handbook guiding principles: knowledge stays immutable, retrieval is deterministic, security before relevance, hybrid retrieval is mandatory, every decision is explainable and observable, ranking is separate from retrieval, and retrieval stays model-independent.

Build order follows the query lifecycle: Foundations, Query Intelligence, Retrieval Execution Core, Workers and Connectors, Candidate Collection and Fusion, Ranking, Context Assembly and Packaging, Observability and Security, then Deployment and EKCP handoff readiness.

## Reference Implementation And Model Strategy
This track uses LangChain and LangGraph as the reference orchestration stack, kept behind engine-owned abstractions to preserve model independence (see [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md)).

Where LangChain and LangGraph are used:
1. Query Intelligence (EKRE-S1): optional LLM-based query understanding, rewrite, and intent classification via ChatPromptTemplate plus PydanticOutputParser and LCEL, behind an engine-owned interpreter seam. Deterministic rule-based understanding remains the default and offline fallback so retrieval stays reproducible.
2. Retrieval Execution Core (EKRE-S2): LangGraph is the execution orchestration engine, using typed graph state, retrieval workers as pure-function nodes, conditional edges for partial-failure degradation, and the Langfuse callback for the stage timeline and trace.
3. Retrieval workers (EKRE-S3): the vector worker accesses embeddings through the Ollama runtime and the Qdrant vector store behind engine-owned worker seams; keyword and metadata workers stay database-native.

Model runtime: Ollama (self-hosted, local-first) for chat and embedding models, inheriting the embedding model and distance metric published by EKIE (no hardcoding). No enterprise data leaves the local environment by default.

Determinism and security: LLM stages are configuration-selectable with deterministic defaults; authorization is always enforced before any LLM or ranking stage so no unauthorized content reaches a model. All model names, hosts, and parameters are configuration-driven.

## Track Definition Of Ready
1. Foundation and EKIE exit gates are approved; EKIE vector payloads and metadata are available.
2. Shared contracts required by EKRE are versioned in packages/contracts, including the security context contract.
3. Distance metric and embedding settings are dynamically inherited from EKIE (no hardcoding in EKRE).
4. EKRE story owners, reviewers, and quality owners are assigned.

## Track Definition Of Done
1. All sprint stories meet acceptance criteria with review evidence.
2. Authorization is enforced before ranking; unauthorized candidates never enter the candidate pool.
3. Retrieval outputs preserve citation lineage (source_path, document_id) end to end and include explainability fields.
4. Retrieval is deterministic: same query against the same knowledge state yields identical results.
5. EKCP handoff evidence package is approved by Product, Architecture, and Quality.

## Success Metrics (Track Level, From Handbook NFRs)
1. Security policy compliance: 100% (authorization enforced before ranking).
2. Citation lineage completeness and explainability coverage: 100% for approved scenarios.
3. End-to-end retrieval latency <= 500 ms for standard queries; stage budgets respected (query understanding < 20 ms, vector retrieval < 150 ms, ranking < 100 ms, context assembly < 50 ms).
4. Service availability >= 99.9% for HA deployment.
5. Retrieval accuracy tracked via Precision@10, Recall@10, MRR, and NDCG.

## EKRE-S0: Retrieval Platform Foundations
Handbook mapping: Chapter 5 (NFR), Chapter 6 (Architecture Overview), Chapter 7 (Query Lifecycle), Chapter 28 (Observability), Chapter 29 (Security baseline).

### Sprint Objective
Establish the retrieval platform substrate: security context handling, observability, configuration, and dynamic inheritance of embedding and distance metric settings from EKIE.

### Scope
1. Security context contract handling for every retrieval request.
2. Distance metric and embedding settings inheritance from EKIE (no hardcoding).
3. Observability baseline: query id, trace id, latency breakdown, stage timeline.
4. Configuration and profile management for retrieval behavior.

### Out Of Scope
1. Ranking model tuning.
2. Chat orchestration behavior.

### Stories
1. EKRE-S0-1 Security context ingress validation contract.
2. EKRE-S0-2 Dynamic distance metric and embedding inheritance from EKIE metadata.
3. EKRE-S0-3 Observability baseline (query id, trace id, latency breakdown).
4. EKRE-S0-4 Retrieval configuration and profile management.

### Deliverables
1. Security context validation contract artifact.
2. Distance metric inheritance design.
3. Observability and configuration baseline.

### Acceptance
1. No hardcoded distance metric or embedding settings in EKRE.
2. Every retrieval request carries a validated security context.
3. Every query exposes trace id and latency breakdown.

### Exit Evidence
1. Approved security context and inheritance design.
2. Observability baseline evidence.

## EKRE-S1: Query Intelligence Domain
Handbook mapping: Chapter 8 (Query Intelligence), Chapter 9 (Query Understanding), Chapter 10 (Intent Classification), Chapter 11 (Query Enrichment), Chapter 12 (Knowledge Awareness Engine), Chapter 13 (Query Planner), plus LLM prompting standards in [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md).

### Sprint Objective
Transform raw queries into planned, enriched, intent-classified retrieval requests with full traceability, using deterministic rules by default and an optional LangChain LLM interpreter behind a stable seam.

### Scope
1. Query understanding and rewrite.
2. Intent classification and query enrichment.
3. Knowledge Awareness Engine and Query Planner.
4. Optional LLM interpreter (ChatPromptTemplate plus PydanticOutputParser via LCEL) behind an engine-owned seam, feature-flagged with a deterministic fallback.

### Out Of Scope
1. Retrieval execution workers.
2. Ranking and context assembly.

### Stories
1. EKRE-S1-1 Query understanding and rewrite engine.
2. EKRE-S1-2 Intent classification engine.
3. EKRE-S1-3 Query enrichment and knowledge awareness.
4. EKRE-S1-4 Query planner and retrieval plan output.
5. EKRE-S1-5 Optional LLM query interpreter (LangChain), feature-flagged with deterministic fallback and validated Pydantic output.

### Deliverables
1. Query understanding and rewrite decision matrix.
2. Intent classification policy artifact.
3. Query plan contract for the execution domain.

### Acceptance
1. Query transformations are traceable and reviewable.
2. Query understanding meets the < 20 ms stage budget target.
3. Ambiguous intent handling is defined and approved.

### Exit Evidence
1. Approved query plan contract.
2. Query intelligence traceability evidence.

## EKRE-S2: Retrieval Execution Core
Handbook mapping: Chapter 14 (Execution Domain Overview), Chapter 15 (Retrieval Orchestrator), Chapter 16 (Execution Runtime), Chapter 17 (Execution Scheduler), Chapter 18 (Retrieval Worker Framework), plus LangGraph standards in [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md).

### Sprint Objective
Deliver the parallel execution core that orchestrates and schedules retrieval workers deterministically as a LangGraph graph.

### Scope
1. Retrieval orchestrator and execution runtime built as a LangGraph graph with typed state and pure-function worker nodes.
2. Execution scheduler and worker framework contracts.
3. Parallel execution and graceful partial-failure handling via conditional edges.

### Out Of Scope
1. Specific worker implementations (next sprint).
2. Fusion and ranking.

### Stories
1. EKRE-S2-1 Retrieval orchestrator design.
2. EKRE-S2-2 Execution runtime and scheduler.
3. EKRE-S2-3 Worker framework contract and lifecycle.
4. EKRE-S2-4 Partial-failure graceful degradation policy.

### Deliverables
1. Orchestrator and runtime design artifact.
2. Worker framework contract.
3. Degradation and retry policy artifact.

### Acceptance
1. Workers execute in parallel where possible.
2. Failed engines do not terminate entire queries.
3. Execution is deterministic for the same knowledge state.

### Exit Evidence
1. Approved execution core design.
2. Degradation behavior validation evidence.

## EKRE-S3: Retrieval Workers And Connectors
Handbook mapping: Chapter 19 (Vector Worker), Chapter 20 (Keyword Worker), Chapter 21 (Metadata Worker), Chapter 22 (Repository Connector Framework), Chapter 29 (Security filtering).

### Sprint Objective
Deliver hybrid retrieval workers with database-level security filtering applied before candidates enter the pool.

### Scope
1. Vector, keyword, and metadata retrieval workers.
2. Repository connector framework with pooling and throttling.
3. Security filtering at the database boundary before candidate collection.
4. Vector worker uses the Ollama embedding runtime and the Qdrant vector store behind engine-owned worker seams, inheriting EKIE distance metric settings.

### Out Of Scope
1. Candidate fusion and ranking.
2. Context assembly.

### Stories
1. EKRE-S3-1 Vector retrieval worker.
2. EKRE-S3-2 Keyword retrieval worker.
3. EKRE-S3-3 Metadata retrieval worker.
4. EKRE-S3-4 Repository connector framework and pre-pool security filtering.

### Deliverables
1. Worker execution contracts for vector, keyword, and metadata paths.
2. Repository connector framework artifact.
3. Pre-ranking authorization filter policy.

### Acceptance
1. Unauthorized candidates never enter the candidate pool.
2. Vector retrieval meets the < 150 ms stage budget target.
3. Distance metric matches EKIE-published settings.

### Exit Evidence
1. Security filtering sequence and negative-path evidence.
2. Worker latency validation evidence.

## EKRE-S4: Candidate Collection And Fusion
Handbook mapping: Chapter 23 (Unified Candidate Collection), Chapter 24 (Candidate Fusion).

### Sprint Objective
Collect multi-source candidates and fuse them with deterministic, explainable strategy.

### Scope
1. Unified candidate collection across workers.
2. Candidate fusion (for example RRF) with tie-break rules.
3. Duplicate minimization and provenance retention.

### Out Of Scope
1. Final ranking and reranking.

### Stories
1. EKRE-S4-1 Unified candidate collection framework.
2. EKRE-S4-2 Candidate fusion policy and tie-break rules.
3. EKRE-S4-3 Duplicate minimization and provenance retention.

### Deliverables
1. Candidate collection contract.
2. Fusion policy artifact with priority and tie-break rules.

### Acceptance
1. Fusion is deterministic and explainable.
2. Source provenance and citation fields are retained through fusion.
3. Candidate fusion meets the < 20 ms stage budget target.

### Exit Evidence
1. Approved fusion policy.
2. Provenance retention evidence.

## EKRE-S5: Ranking Engine
Handbook mapping: Chapter 25 (Ranking Engine).

### Sprint Objective
Deliver auditable ranking and reranking that is separate from retrieval execution.

### Scope
1. Ranking and reranking pipeline behavior.
2. Ranking factor transparency and audit fields.
3. Configurable candidate limits.

### Out Of Scope
1. Context assembly and packaging.

### Stories
1. EKRE-S5-1 Ranking pipeline and scoring model.
2. EKRE-S5-2 Reranking behavior and audit field map.
3. EKRE-S5-3 Configurable candidate limits and performance controls.

### Deliverables
1. Ranking and reranking policy artifact.
2. Ranking audit field map.

### Acceptance
1. Ranking decisions are auditable and explainable.
2. Ranking meets the < 100 ms stage budget target.
3. Ranking remains separate from retrieval execution.

### Exit Evidence
1. Approved ranking policy.
2. Ranking audit evidence.

## EKRE-S6: Context Assembly And Response Packaging
Handbook mapping: Chapter 26 (Context Assembly), Chapter 27 (Response Packaging and Handoff).

### Sprint Objective
Assemble citation-preserving context and package a structured retrieval result for EKCP.

### Scope
1. Context assembly with citation lineage guarantees.
2. Response packaging and handoff contract.
3. Explainability payload finalization.

### Out Of Scope
1. EKCP response generation.

### Stories
1. EKRE-S6-1 Context assembly with citation non-drop controls.
2. EKRE-S6-2 Response packaging and handoff contract.
3. EKRE-S6-3 Explainability payload finalization.

### Deliverables
1. Context assembly design with citation guarantees.
2. Response package contract for EKCP.
3. Explainability payload schema.

### Acceptance
1. Citation lineage (source_path, document_id) is never dropped.
2. Context assembly meets the < 50 ms stage budget target.
3. Response package contract is consumable by EKCP.

### Exit Evidence
1. Citation persistence validation report.
2. Approved response package contract.

## EKRE-S7: Observability, Security, Governance And Compliance
Handbook mapping: Chapter 28 (Observability and Traceability), Chapter 29 (Security, Governance and Compliance).

### Sprint Objective
Harden end-to-end traceability, security enforcement, and compliance across the retrieval pipeline.

### Scope
1. End-to-end query traceability and metrics.
2. Centralized security policy management and audit logging.
3. Compliance controls and sensitive metadata protection.

### Out Of Scope
1. EKCP governance behavior.

### Stories
1. EKRE-S7-1 End-to-end traceability and metrics.
2. EKRE-S7-2 Centralized security policy and audit logging.
3. EKRE-S7-3 Compliance and sensitive metadata protection.

### Deliverables
1. Traceability and metrics evidence template.
2. Security and compliance control matrix.

### Acceptance
1. Every query exposes a complete execution timeline and latency breakdown.
2. Security-relevant events are audited.
3. Sensitive metadata is protected.

### Exit Evidence
1. Traceability evidence pack.
2. Security and compliance control evidence.

## EKRE-S8: Deployment, Scalability And EKCP Handoff Readiness
Handbook mapping: Chapter 30 (Deployment Architecture and Scalability), Chapter 5 (NFR validation).

### Sprint Objective
Prove scalability, availability, and readiness for EKCP handoff.

### Scope
1. Independent service deployment and worker-pool scaling.
2. High availability, failover, and circuit breakers.
3. Multi-tenant, tenant-aware scheduling and observability.
4. Retrieval accuracy and latency validation.

### Out Of Scope
1. EKCP and master integration execution.

### Stories
1. EKRE-S8-1 Service deployment and worker-pool autoscaling.
2. EKRE-S8-2 HA, failover, and circuit-breaker validation.
3. EKRE-S8-3 Multi-tenant scheduling and tenant-aware observability.
4. EKRE-S8-4 Accuracy and latency validation (Precision@10, Recall@10, MRR, NDCG, <= 500 ms).
5. EKRE-S8-5 EKCP handoff readiness package.

### Deliverables
1. Deployment and scaling design with evidence.
2. HA and failover validation package.
3. Accuracy and latency evidence package.
4. EKCP handoff package with citation and security proof.

### Acceptance
1. Availability >= 99.9% and end-to-end latency <= 500 ms are demonstrated.
2. Retrieval accuracy metrics meet approved thresholds.
3. HA and graceful degradation are validated.

### Exit Evidence
1. Signed deployment, HA, and accuracy validation packages.
2. Product, Architecture, and Quality sign-off for EKCP handoff.

## Risk Register (Track Level)
1. Risk: rewrite policy drift reduces retrieval predictability. Mitigation: freeze rewrite rules per sprint and review changes at sprint boundaries (EKRE-S1).
2. Risk: security filtering regressions expose unauthorized candidates. Mitigation: enforce pre-pool authorization checks in EKRE-S3 acceptance evidence.
3. Risk: citation lineage gaps block EKCP readiness. Mitigation: require citation persistence report as hard exit artifact in EKRE-S6.
4. Risk: hardcoded distance metric breaks vector math consistency. Mitigation: enforce dynamic inheritance from EKIE in EKRE-S0.
5. Risk: latency budgets exceeded under load. Mitigation: validate stage budgets and end-to-end <= 500 ms in EKRE-S8.
6. Risk: LLM query interpretation introduces non-determinism or unauthorized data exposure. Mitigation: keep the LLM interpreter configuration-selectable with deterministic defaults, enforce authorization before any model call, and validate LLM output against Pydantic schemas (EKRE-S1).

## Reporting Cadence
1. Weekly sprint review with Product, Architecture, and Quality.
2. Mid-sprint dependency review focused on EKCP handoff blockers.
3. End-sprint gate review with explicit go or hold decision.

## Sprint Board Backlog (Ready To Use)

### EKRE-S0 Foundations
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S0-1 | Security context ingress validation | High | Security Owner | T-Shirt M | EKIE gate | Approved validation contract |
| EKRE-S0-2 | Distance metric inheritance from EKIE | High | Retrieval Architect | T-Shirt M | EKRE-S0-1 | Inheritance design approved |
| EKRE-S0-3 | Observability baseline | High | Observability Owner | T-Shirt S | EKRE-S0-1 | Trace and latency baseline |
| EKRE-S0-4 | Retrieval configuration and profiles | Medium | Platform Owner | T-Shirt S | EKRE-S0-1 | Config baseline approved |

### EKRE-S1 Query Intelligence
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S1-1 | Query understanding and rewrite | High | EKRE Lead | T-Shirt M | EKRE-S0 Exit | Approved rewrite matrix |
| EKRE-S1-2 | Intent classification | High | Retrieval PM | T-Shirt M | EKRE-S1-1 | Approved intent policy |
| EKRE-S1-3 | Enrichment and knowledge awareness | Medium | Retrieval Architect | T-Shirt M | EKRE-S1-1 | Enrichment design approved |
| EKRE-S1-4 | Query planner and plan contract | High | Retrieval Architect | T-Shirt M | EKRE-S1-2 | Approved query plan contract |
| EKRE-S1-5 | Optional LLM query interpreter (LangChain) | Medium | Retrieval Architect | T-Shirt M | EKRE-S1-4 | Deterministic-default parity evidence |

### EKRE-S2 Execution Core
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S2-1 | Retrieval orchestrator | High | EKRE Lead | T-Shirt M | EKRE-S1 Exit | Approved LangGraph orchestrator design |
| EKRE-S2-2 | Runtime and scheduler | High | Platform Owner | T-Shirt M | EKRE-S2-1 | Approved LangGraph runtime design |
| EKRE-S2-3 | Worker framework contract | High | Retrieval Architect | T-Shirt M | EKRE-S2-1 | Approved worker contract |
| EKRE-S2-4 | Partial-failure degradation | Medium | Reliability Owner | T-Shirt S | EKRE-S2-2 | Degradation evidence |

### EKRE-S3 Workers And Connectors
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S3-1 | Vector retrieval worker | High | Retrieval Architect | T-Shirt M | EKRE-S2 Exit | Vector worker validated |
| EKRE-S3-2 | Keyword retrieval worker | High | Retrieval Architect | T-Shirt M | EKRE-S2 Exit | Keyword worker validated |
| EKRE-S3-3 | Metadata retrieval worker | Medium | Data Platform Owner | T-Shirt M | EKRE-S2 Exit | Metadata worker validated |
| EKRE-S3-4 | Connectors and pre-pool security filtering | High | Security Owner | T-Shirt M | EKRE-S3-1 | Pre-pool filter evidence |

### EKRE-S4 Candidate Fusion
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S4-1 | Unified candidate collection | High | Retrieval Architect | T-Shirt M | EKRE-S3 Exit | Collection contract approved |
| EKRE-S4-2 | Candidate fusion policy | High | Ranking Owner | T-Shirt M | EKRE-S4-1 | Fusion policy approval |
| EKRE-S4-3 | Duplicate minimization and provenance | Medium | Retrieval Architect | T-Shirt S | EKRE-S4-2 | Provenance evidence |

### EKRE-S5 Ranking
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S5-1 | Ranking pipeline and scoring | High | Ranking Owner | T-Shirt M | EKRE-S4 Exit | Ranking policy approval |
| EKRE-S5-2 | Reranking and audit fields | High | Ranking Owner | T-Shirt M | EKRE-S5-1 | Audit field map approved |
| EKRE-S5-3 | Configurable candidate limits | Medium | Platform Owner | T-Shirt S | EKRE-S5-1 | Limit policy approved |

### EKRE-S6 Context Assembly And Packaging
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S6-1 | Context assembly with citation controls | High | Retrieval Architect | T-Shirt M | EKRE-S5 Exit | Citation persistence report |
| EKRE-S6-2 | Response packaging and handoff contract | High | API Contract Owner | T-Shirt M | EKRE-S6-1 | Approved package contract |
| EKRE-S6-3 | Explainability payload finalization | Medium | API Contract Owner | T-Shirt S | EKRE-S6-1 | Payload sample review |

### EKRE-S7 Observability And Security
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S7-1 | End-to-end traceability and metrics | High | Observability Owner | T-Shirt M | EKRE-S6 Exit | Traceability evidence |
| EKRE-S7-2 | Centralized security policy and audit | High | Security Owner | T-Shirt M | EKRE-S7-1 | Audit evidence |
| EKRE-S7-3 | Compliance and sensitive metadata protection | Medium | Governance Owner | T-Shirt S | EKRE-S7-1 | Compliance evidence |

### EKRE-S8 Deployment And Handoff
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKRE-S8-1 | Service deployment and worker-pool autoscaling | High | DevOps Owner | T-Shirt M | EKRE-S7 Exit | Deployment evidence |
| EKRE-S8-2 | HA, failover, and circuit breakers | High | Reliability Owner | T-Shirt M | EKRE-S8-1 | HA validation |
| EKRE-S8-3 | Multi-tenant scheduling and observability | Medium | Platform Owner | T-Shirt M | EKRE-S8-1 | Tenant-aware evidence |
| EKRE-S8-4 | Accuracy and latency validation | High | Quality Lead | T-Shirt M | EKRE-S8-1 | Accuracy and latency pack |
| EKRE-S8-5 | EKCP handoff readiness package | High | EKRE Lead | T-Shirt M | EKRE-S8-4 | Signed EKCP handoff artifact |

## Track Dependencies
1. Must run after EKIE sprint exit gate.
2. EKCP cannot start until EKRE citation and security gate passes.

## Track Exit Gate
1. EKRE citation, security, accuracy, and deployment readiness gate approved by Product, Architecture, and Quality.

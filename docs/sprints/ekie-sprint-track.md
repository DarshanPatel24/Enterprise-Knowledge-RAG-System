# EKIE Sprint Track

> Track Owner: EKIE Engine Lead
> Start Condition: Foundation sprint exit gate passed
> Objective: Deliver EKIE as a deterministic, governed, observable ingestion platform that converts enterprise documents into versioned, AI-ready knowledge assets and publishes complete vector payloads for EKRE.
> Source Of Truth: [../EKIE/EKIE-handbook.md](../EKIE/EKIE-handbook.md)

## Alignment To Handbook
This track is decomposed directly from the EKIE Enterprise Architecture Handbook frameworks. Each sprint maps to specific handbook chapters and enforces the handbook core principles: canonical Markdown representation, immutable versioned assets, deterministic processing, Control Plane as source of truth, digital twin architecture, event-driven workflows, configuration over code, and observability by default.

Build order follows the ingestion lifecycle: Foundations, Repository Sync, Transformation, Document Intelligence, Chunking, Embedding, Vector Publishing, Workflow Orchestration, Security and Extensibility, then Testing and Deployment readiness.

## Reference Implementation And Model Strategy
This track uses LangChain and LangGraph as the reference orchestration stack, kept behind engine-owned abstractions to preserve model independence (see [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md)).

Where LangChain and LangGraph are used:
1. LLM-based Document Intelligence (EKIE-S3 enhancement): optional LLM semantic enrichment via ChatPromptTemplate plus an output parser and LCEL, built behind the existing Analyzer plugin seam. Rule-based analyzers remain the deterministic default and offline fallback.
2. Workflow Orchestration (EKIE-S7): LangGraph is the orchestration engine, using typed graph state, nodes as pure functions over state, a checkpointer for resume-from-checkpoint recovery, and the Langfuse callback for tracing.

Where LangChain is intentionally not used, to avoid double abstraction over existing seams:
1. Embedding generation: real models are accessed through the existing EmbeddingProvider abstraction. A real Ollama embedding provider (for example nomic-embed-text or mxbai-embed-large) is added behind that seam; the deterministic hash provider remains the test and offline default.
2. Vector publishing: the vector database is accessed through the existing VectorProvider abstraction (qdrant-client); the in-memory provider remains the test default.

Model runtime: Ollama (self-hosted, local-first) for both chat and embedding models. No enterprise data leaves the local environment by default. All model names, hosts, and parameters are configuration-driven and selected per environment.

Determinism and testing: LLM and real-model stages are configuration-selectable. Deterministic providers remain the default for the automated test suite so pipeline tests stay fast, offline, and reproducible.

> Delivery status (2026-07-01): The settings-driven composition root (services/ekie/src/composition.py) and the S3-5, S5-5, and S6-5 enhancement stories are delivered and Approved (validated: ruff, mypy --strict, 161 pytest green). Real providers (Ollama, Qdrant) and the optional LLM analyzer are selected only by configuration; deterministic providers remain the offline and test defaults.

## Track Definition Of Ready
1. Foundation sprint exit gate is approved and shared contracts are versioned in packages/contracts.
2. Control Plane (SQL Server), object storage, vector database (Qdrant), and cache (Redis) targets are provisioned for the environment.
3. EKIE story owners, reviewers, and quality owners are assigned.
4. Repository source priorities and supported Phase 1 file types are confirmed by Product.

## Track Definition Of Done
1. All sprint stories meet acceptance criteria with review evidence.
2. Ingestion is deterministic: same document plus same policy yields identical Markdown, chunks, and embeddings.
3. Vector payloads carry complete mandatory metadata (document_id, chunk_id, tenant_id, classification_clearance, distance_metric) and full asset lineage.
4. Pipeline-level tests pass end to end from repository sync through vector publication.
5. EKRE handoff evidence package is approved by Product, Architecture, and Quality.

## Success Metrics (Track Level, From Handbook NFRs)
1. Workflow Success Rate >= 99.5%.
2. Platform Availability >= 99.95% for HA deployment.
3. Synchronization accuracy: 100% for detected changes.
4. Markdown generation < 5s per average document; chunk generation < 2s per document; publish verification < 1s per asset.
5. Asset lineage completeness: 100% with no broken lineage chains.
6. Deterministic transformation consistency: 100% for approved scenarios.

## EKIE-S0: Platform Foundations And Control Plane
> Status: Approved (validated: ruff, mypy --strict, pytest green).

Handbook mapping: Chapter 2 (Principles), Chapter 5 (Digital Twin), Chapter 13 (Control Plane and Metadata), Chapter 14 (Storage), Chapter 15 (Config and Policy), Chapter 16 (Observability).

### Sprint Objective
Establish the shared platform substrate so every later framework has Control Plane state, versioned storage, configuration, and observability from day one.

### Scope
1. Control Plane schema for repositories, documents, assets, workflows, lineage, and processing state.
2. Configuration and Policy engine baseline (configuration over code, versioned policies).
3. Storage abstraction for immutable, versioned assets.
4. Observability baseline: structured logs, metrics, traces, health with tenant_id and correlation_id.

### Out Of Scope
1. Retrieval, ranking, and chat behavior.
2. Document transformation logic (delivered in later sprints).

### Stories
1. EKIE-S0-1 Control Plane metadata schema and migrations.
2. EKIE-S0-2 Configuration and Policy engine baseline with environment-backed settings.
3. EKIE-S0-3 Immutable versioned asset storage abstraction.
4. EKIE-S0-4 Observability baseline (logs, metrics, traces, health).

### Deliverables
1. Control Plane schema and metadata service interface.
2. Configuration model and policy resolution baseline.
3. Storage service contract for asset persistence and versioning.
4. Observability conventions and instrumentation baseline.

### Acceptance
1. Control Plane is the single source of truth for ingestion state.
2. No hardcoded operational values; all tunables are configuration-driven.
3. Every processing stage can emit logs, metrics, and traces.

### Exit Evidence
1. Approved Control Plane schema and migration plan.
2. Approved configuration and observability baseline.

## EKIE-S1: Repository Synchronization Framework
> Status: Approved (validated: ruff, mypy --strict, 42 pytest green). Code in services/ekie/src/domain/sync.

Handbook mapping: Chapter 6 (Repository Synchronization), Chapter 5 (Document lifecycle and change detection).

### Sprint Objective
Continuously synchronize enterprise repositories and maintain accurate Document Digital Twins with reliable change detection.

### Scope
1. Repository connector framework and registration.
2. Scan strategy: incremental and reconciliation scans.
3. Change detection: create, modify, rename, move, delete via hashing.
4. Repository and document synchronization state machines.

### Out Of Scope
1. Document parsing and Markdown generation.
2. Embedding and publishing.

### Stories
1. EKIE-S1-1 Connector abstraction, registration, and metadata.
2. EKIE-S1-2 Document Digital Twin model and state machine.
3. EKIE-S1-3 Change detection with hashing, rename and move detection.
4. EKIE-S1-4 Reconciliation and synchronization policies.

### Deliverables
1. Connector contract and adapter policy artifact.
2. Document Twin lifecycle and transition model.
3. Change detection and reconciliation design with generated sync events.

### Acceptance
1. Twin lifecycle covers active, archived, and deleted states with versioning.
2. Detected source changes reconcile at 100% accuracy for approved scenarios.
3. Sync failures are retryable and recoverable.

### Exit Evidence
1. Approved synchronization state machines and event contracts.
2. Change-detection accuracy validation for approved scenarios.

## EKIE-S2: Document Transformation And Canonical Markdown
> Status: Approved (validated: ruff, mypy --strict, 67 pytest green). Code in services/ekie/src/domain/transformation.

Handbook mapping: Chapter 7 (Transformation and Canonical Markdown).

### Sprint Objective
Deterministically transform heterogeneous Phase 1 file types into canonical, validated Markdown with extracted metadata.

### Scope
1. Parser registry and transformation pipeline.
2. Normalization rules and canonical Markdown structure standard.
3. Table, image, OCR, and embedded object handling.
4. Transformation validation and asset versioning.

### Out Of Scope
1. Semantic document intelligence scoring (next sprint).
2. Chunking and embedding.

### Stories
1. EKIE-S2-1 Parser registry and transformation pipeline.
2. EKIE-S2-2 Canonical Markdown normalization and structure standard.
3. EKIE-S2-3 Table, image, and OCR handling.
4. EKIE-S2-4 Transformation validation and versioned Markdown assets.

### Deliverables
1. Canonical Markdown standard and normalization rules artifact.
2. Parser registry contract for Phase 1 file types.
3. Markdown validation framework and versioning policy.

### Acceptance
1. Same input plus same configuration yields identical Markdown output.
2. Markdown generation meets the < 5s per average document target.
3. Markdown assets are immutable and versioned with metadata.

### Exit Evidence
1. Determinism validation report for Markdown generation.
2. Approved canonical Markdown standard and validation results.

## EKIE-S3: Document Intelligence Framework
> Status: Approved (validated: ruff, mypy --strict, 83 pytest green). Code in services/ekie/src/domain/intelligence.
Handbook mapping: Chapter 8 (Document Intelligence).

### Sprint Objective
Enrich canonical Markdown with structural and semantic intelligence to improve downstream chunk quality.

### Scope
1. Structure analysis, section and table intelligence.
2. Figure, code block, and language detection.
3. Content classification and sensitive content detection.
4. Document quality scoring and semantic metadata output contract.

### Out Of Scope
1. Chunk generation (next sprint).
2. Embedding generation.

### Stories
1. EKIE-S3-1 Structure and section intelligence.
2. EKIE-S3-2 Table, figure, and code detection.
3. EKIE-S3-3 Content classification and sensitive content detection.
4. EKIE-S3-4 Document quality score and semantic metadata contract.

### Deliverables
1. Document intelligence output contract for chunking.
2. Sensitive content detection policy artifact.
3. Quality scoring rules and evidence template.

### Acceptance
1. Intelligence output contract is consumable by the chunking framework.
2. Sensitive content is flagged consistently for governed handling.

### Exit Evidence
1. Approved document intelligence output contract.
2. Classification and sensitivity validation evidence.

### Planned Enhancement: LLM-Based Intelligence (LangChain)
> Status: Approved (validated: ruff, mypy --strict, 161 pytest green). Code in services/ekie/src/domain/intelligence (llm.py, prompts.py, analyzers/llm.py). Additive to the approved rule-based analyzers; feature-flagged and off by default.

1. EKIE-S3-5 LLM analyzer plugin using ChatPromptTemplate plus an output parser (LCEL) to refine the document primary topic, built behind the existing Analyzer seam and degrading gracefully to the deterministic result on model unavailability. Broader LLM classification and semantic tagging remain available for future extension behind the same seam.

Acceptance:
1. The LLM analyzer is selectable by configuration; rule-based analyzers remain the default.
2. LLM output is validated against Pydantic v2 models and reuses packages/contracts types where cross-engine.
3. With the LLM analyzer disabled, S3 output remains identical to the approved deterministic baseline.

## EKIE-S4: Intelligent Chunking Framework
> Status: Approved (validated: ruff, mypy --strict, 99 pytest green). Code in services/ekie/src/domain/chunking.
Handbook mapping: Chapter 9 (Intelligent Chunking).

### Sprint Objective
Produce structure-aware, semantically coherent chunks with complete lineage and identity.

### Scope
1. Section-aware, table-aware, and code-aware chunking strategies.
2. Semantic boundary detection and context preservation.
3. Token budget management and chunk identity and versioning.
4. Chunk validation rules.

### Out Of Scope
1. Embedding generation and vector publishing.

### Stories
1. EKIE-S4-1 Chunking strategies and semantic boundary detection.
2. EKIE-S4-2 Token budget management and context preservation.
3. EKIE-S4-3 Chunk identity, versioning, and lineage metadata.
4. EKIE-S4-4 Chunk validation rules (no empty chunks, token limits).

### Deliverables
1. Chunking policy artifact with boundary and overlap rules.
2. Chunk metadata and identity model.
3. Chunk validation checklist and evidence template.

### Acceptance
1. Same input plus same policy yields stable chunk outputs.
2. Chunk generation meets the < 2s per document target.
3. Chunks carry lineage back to source document and Markdown asset.

### Exit Evidence
1. Determinism and lineage validation for chunks.
2. Approved chunking policy and validation results.

## EKIE-S5: Embedding Framework
Handbook mapping: Chapter 10 (Embedding Framework).

> Status: Approved (validated: ruff, mypy --strict, 114 pytest green). Code in services/ekie/src/domain/embedding.

### Sprint Objective
Generate version-controlled embeddings through a provider-abstracted, deterministic embedding pipeline.

### Scope
1. Embedding asset model and provider abstraction.
2. Embedding model registry and selection policy.
3. Embedding workflow, token management, and batching.
4. Embedding version control and distance metric declaration.

### Out Of Scope
1. Vector publishing (next sprint).
2. Retrieval-side distance metric usage.

### Stories
1. EKIE-S5-1 Provider abstraction and model registry.
2. EKIE-S5-2 Embedding workflow, token management, and batching.
3. EKIE-S5-3 Embedding asset versioning and metadata (model, distance_metric).
4. EKIE-S5-4 Embedding validation (dimensionality, zero-vector detection).

### Deliverables
1. Provider abstraction contract and model registry.
2. Embedding orchestration workflow artifact.
3. Embedding validation checklist and evidence template.

### Acceptance
1. Embedding outputs are dimensionally correct and model-consistent.
2. Embedding assets are versioned and carry model and distance metric metadata.
3. Embedding throughput respects provider limits via batching.

### Exit Evidence
1. Embedding validation evidence (dimensionality, consistency).
2. Approved embedding asset and metadata model.

### Planned Enhancement: Real Embedding Model (Ollama)
> Status: Approved (validated: ruff, mypy --strict, 161 pytest green). Code in services/ekie/src/domain/embedding/providers/ollama.py. Additive behind the approved EmbeddingProvider seam; the hash provider stays the test default.

1. EKIE-S5-5 Ollama embedding provider (for example nomic-embed-text) selected via configuration, producing real semantic vectors; the deterministic hash provider remains the offline and test default.

Acceptance:
1. The provider is selectable by configuration with no change to the embedding workflow.
2. Vector dimension and distance metric are sourced from the model registry, not hardcoded.
3. The test suite continues to run offline and deterministically on the default provider.

## EKIE-S6: Vector Publishing Framework
Handbook mapping: Chapter 11 (Vector Publishing).

> Status: Approved (validated: ruff, mypy --strict, 133 pytest green). Code in services/ekie/src/domain/publishing.

### Sprint Objective
Publish vectors reliably to the vector database with the enforced collection schema and complete metadata.

### Scope
1. Vector Database Collection Schema enforcement.
2. Mandatory metadata mapping (document_id, chunk_id, tenant_id, classification_clearance, distance_metric).
3. Publish validation, idempotency, and retry policy.
4. Publish verification and lineage closure.

### Out Of Scope
1. Retrieval queries against published vectors.

### Stories
1. EKIE-S6-1 Collection schema enforcement and payload mapping.
2. EKIE-S6-2 Idempotent publish with retry and failure handling.
3. EKIE-S6-3 Publish verification and lineage closure.
4. EKIE-S6-4 Required-field validation gate before publish.

### Deliverables
1. Vector payload required-fields map and schema enforcement artifact.
2. Publish validation and retry policy artifact.
3. Publish verification evidence template.

### Acceptance
1. Every published vector carries complete mandatory metadata.
2. Publish verification meets the < 1s per asset target.
3. Publish is idempotent and recoverable on failure.

### Exit Evidence
1. Required-field and schema validation evidence.
2. Publish verification and idempotency review sign-off.

### Planned Enhancement: Real Vector Database (Qdrant)
> Status: Approved (validated: ruff, mypy --strict, 161 pytest green). Code in services/ekie/src/domain/publishing/providers/qdrant.py. Additive behind the approved VectorProvider seam; the in-memory provider stays the test default.

1. EKIE-S6-5 Qdrant vector provider (qdrant-client) selected via configuration; the in-memory provider remains the test default. Verification, lineage, and idempotency behavior are unchanged.

## EKIE-S7: Workflow Orchestration And Recovery
Handbook mapping: Chapter 12 (Workflow Orchestration), Chapter 5 (workflow relationship), plus LangGraph standards in [../../.github/instructions/langchain.instructions.md](../../.github/instructions/langchain.instructions.md).

### Sprint Objective
Orchestrate the end-to-end ingestion workflow as a LangGraph graph with checkpoints, retries, and lineage-aware replay.

> Status: Approved (validated: ruff, mypy --strict, 187 pytest green). Code in services/ekie/src/domain/orchestration (typed WorkflowState, pure-function stage nodes, checkpointer, sequential + LangGraph runners) and services/ekie/src/api (ingestion router wired to the composition root). The deterministic sequential runner is the offline/test default; the LangGraph runner and Langfuse tracing are additive behind a lazy import and selected only by configuration. Demo: services/ekie/scripts/demo_orchestration.py.

### Scope
1. LangGraph orchestration engine: typed graph state, nodes as pure functions over state, a checkpointer for recovery, and Langfuse tracing.
2. Workflow definition across sync, transform, intelligence, chunk, embed, publish.
3. Checkpointing, dead-letter handling, and lease recovery.
4. Event-driven execution and idempotent task processing.
5. Reconciliation and lineage-aware replay.

### Out Of Scope
1. Multi-region failover execution (deployment readiness sprint).

### Stories
1. EKIE-S7-1 Workflow definition and task orchestration as a LangGraph graph.
2. EKIE-S7-2 Checkpointing and resume-from-checkpoint recovery using a LangGraph checkpointer.
3. EKIE-S7-3 Dead-letter handling and retry policy.
4. EKIE-S7-4 Lineage-aware replay and reconciliation.

### Deliverables
1. LangGraph graph and typed state model with the workflow orchestration task graph.
2. Recovery and checkpoint policy artifact.
3. Replay and reconciliation design.

### Acceptance
1. Interrupted workflows resume from checkpoint with no duplicate execution.
2. Workflow Success Rate target >= 99.5% is demonstrable in tests.
3. No data loss on simulated worker crash.

### Exit Evidence
1. Checkpoint recovery validation report.
2. Approved workflow orchestration and recovery design.

## EKIE-S8: Security, Governance And Extensibility
Handbook mapping: Chapter 17 (Security and Governance), Chapter 18 (Plugin and Extension SDK).

### Sprint Objective
Enforce zero-trust security, governance, and safe plugin extensibility across the pipeline.

> Status: Approved (validated: ruff, mypy --strict, 239 pytest green). Code in services/ekie/src/domain/security (authentication, RBAC + ABAC authorization, ephemeral secrets with log redaction, append-only audit, monotonic classification propagation, per-stage StagePolicyGuard) and services/ekie/src/domain/plugins (manifest + semantic-version compatibility, sandboxed execution with error containment, mandatory pre-activation validation, controlled activation-gated registry). Composition builders (build_security_policy/build_secret_provider/build_stage_guard/build_plugin_registry) and log redaction wired in the API app factory. Deterministic and dependency-free; local-first defaults keep the offline path open. Demo: services/ekie/scripts/demo_security.py.

### Scope
1. Authentication, authorization, encryption, and secret management.
2. Audit logging and policy enforcement per stage.
3. Plugin SDK with sandboxed validation before activation.
4. Classification clearance propagation into asset metadata.

### Out Of Scope
1. Downstream retrieval security enforcement (EKRE track).

### Stories
1. EKIE-S8-1 AuthN, AuthZ, encryption, and secret management.
2. EKIE-S8-2 Audit logging and per-stage policy enforcement.
3. EKIE-S8-3 Plugin SDK and pre-activation sandbox validation.
4. EKIE-S8-4 Classification clearance propagation and governance evidence.

### Deliverables
1. Security and governance control matrix.
2. Plugin validation and activation policy.
3. Audit and classification evidence template.

### Acceptance
1. No secrets exposed in logs; policy enforced at each stage.
2. No plugin activates without passing sandbox validation.
3. Classification clearance is present on published assets.

### Exit Evidence
1. Security and governance control evidence.
2. Plugin validation sign-off.

## EKIE-S9: Testing, Validation And Deployment Readiness
Handbook mapping: Chapter 19 (Deployment), Chapter 20 (Testing and Validation), Chapter 21 (Disaster Recovery), Chapter 22 (Operations).

### Sprint Objective
Prove correctness, resilience, and production readiness across the full ingestion pipeline and prepare EKRE handoff.

> Status: Approved (validated: ruff, mypy --strict, 252 pytest green). Code in services/ekie/src/domain/validation (structured findings/reports, read-back asset loaders, per-facet validators for workflow/lineage/chunks/embeddings/vectors, end-to-end PipelineValidator, deterministic load harness with success-rate/throughput/latency percentiles, injectable failure simulation, deployment/HA/DR readiness assessment, and the EKRE HandoffPackage builder). DeploymentSettings adds env-driven NFR and RPO/RTO targets; build_pipeline_validator wired in the composition root. Deterministic and dependency-free; local-first readiness requires no Kubernetes. Demo: services/ekie/scripts/demo_validation.py.

### Scope
1. Testing layers: unit, component, integration, pipeline, system, production validation.
2. Data validation, chunk quality, embedding, and workflow validation.
3. Load and stress testing at enterprise scale; failure simulation.
4. Deployment readiness: Kubernetes, CI/CD gates, HA, DR RPO/RTO.

### Out Of Scope
1. EKRE, EKCP, and master integration execution.

### Stories
1. EKIE-S9-1 Pipeline-level end-to-end validation suite.
2. EKIE-S9-2 Data, chunk, embedding, and workflow validations.
3. EKIE-S9-3 Load, stress, and failure-simulation coverage.
4. EKIE-S9-4 Deployment, CI/CD gate, HA, and DR readiness evidence.
5. EKIE-S9-5 EKRE handoff readiness package.

### Deliverables
1. Full pipeline validation suite and results.
2. Load and stress test evidence package.
3. Deployment and DR readiness checklist with RPO/RTO evidence.
4. EKRE handoff package with quality and lineage proof.

### Acceptance
1. Pipeline tests pass end to end with no data loss or broken lineage.
2. NFR targets are demonstrated (success rate, latency budgets, availability).
3. Deployment, HA, and DR criteria are validated for the target environment.

### Exit Evidence
1. Signed pipeline, load, and DR validation packages.
2. Product, Architecture, and Quality sign-off for EKRE handoff.

## Risk Register (Track Level)
1. Risk: connector variance causes ingestion inconsistency. Mitigation: enforce adapter contract and reconciliation reviews in EKIE-S1.
2. Risk: non-deterministic transformation or chunking degrades retrieval quality. Mitigation: enforce determinism validation gates in EKIE-S2 and EKIE-S4.
3. Risk: incomplete vector metadata blocks EKRE. Mitigation: enforce required-field validation gate in EKIE-S6.
4. Risk: workflow failures cause data loss. Mitigation: enforce checkpoint and lineage-aware replay in EKIE-S7.
5. Risk: security or classification gaps break governance. Mitigation: enforce per-stage policy and clearance propagation in EKIE-S8.
6. Risk: LLM non-determinism or local model unavailability degrades reproducibility. Mitigation: keep providers configuration-selectable, retain deterministic defaults in tests, and validate LLM output against Pydantic schemas.

## Post-Track Enhancement: DSAR Batch Purge (2026-07-08)

> Status: Approved (ruff + mypy --strict clean, 320 pytest green). Added `POST /v1/documents/purge` in `services/ekie/src/api/ingestion.py` for GDPR/DSAR execution: a tenant-scoped batch that hard-deletes a supplied set of document ids (reusing `DocumentDeletionService` with `force=true`, reporting `missing` ids for idempotency). This closes Master Integration risk R2/M2-D1; the integration `PurgeOrchestrator` fans an `EnterpriseDataPurgeEvent` to this endpoint. Note: EKIE data is tenant + document scoped (no user attribution), so the DSAR subscriber resolves the subject's document set upstream.

## Reporting Cadence
1. Weekly sprint review with Product, Architecture, and Quality.
2. Mid-sprint dependency review focused on downstream EKRE handoff blockers.
3. End-sprint gate review with explicit go or hold decision.

## Sprint Board Backlog (Ready To Use)

### EKIE-S0 Foundations
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S0-1 | Control Plane metadata schema and migrations | High | Control Plane Owner | T-Shirt M | Foundation gate | Approved schema and migrations |
| EKIE-S0-2 | Config and Policy engine baseline | High | Platform Owner | T-Shirt M | EKIE-S0-1 | Config baseline approved |
| EKIE-S0-3 | Immutable versioned asset storage | High | Storage Owner | T-Shirt M | EKIE-S0-1 | Storage contract approved |
| EKIE-S0-4 | Observability baseline | High | Observability Owner | T-Shirt S | EKIE-S0-1 | Instrumentation baseline approved |

### EKIE-S1 Repository Synchronization
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S1-1 | Connector abstraction and registration | High | EKIE Lead | T-Shirt M | EKIE-S0 Exit | Approved connector contract |
| EKIE-S1-2 | Document Twin model and state machine | High | Data Model Owner | T-Shirt M | EKIE-S1-1 | Approved twin lifecycle |
| EKIE-S1-3 | Change detection with hashing | High | Platform Owner | T-Shirt M | EKIE-S1-2 | Change accuracy evidence |
| EKIE-S1-4 | Reconciliation and sync policies | Medium | Platform Owner | T-Shirt S | EKIE-S1-3 | Approved reconciliation design |

### EKIE-S2 Transformation And Markdown
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S2-1 | Parser registry and pipeline | High | Transform Owner | T-Shirt M | EKIE-S1 Exit | Approved parser registry |
| EKIE-S2-2 | Canonical Markdown standard | High | Transform Owner | T-Shirt M | EKIE-S2-1 | Approved Markdown standard |
| EKIE-S2-3 | Table, image, and OCR handling | Medium | Content Owner | T-Shirt M | EKIE-S2-2 | Handling policy approved |
| EKIE-S2-4 | Markdown validation and versioning | High | Quality Lead | T-Shirt S | EKIE-S2-2 | Determinism report |

### EKIE-S3 Document Intelligence
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S3-1 | Structure and section intelligence | High | Content Intelligence Owner | T-Shirt M | EKIE-S2 Exit | Structure output approved |
| EKIE-S3-2 | Table, figure, code detection | Medium | Content Intelligence Owner | T-Shirt M | EKIE-S3-1 | Detection evidence |
| EKIE-S3-3 | Classification and sensitive detection | High | Governance Owner | T-Shirt M | EKIE-S3-1 | Sensitivity policy approved |
| EKIE-S3-4 | Quality score and metadata contract | High | Content Intelligence Owner | T-Shirt S | EKIE-S3-1 | Output contract approved |
| EKIE-S3-5 | LLM analyzer plugin (LangChain), feature-flagged | Medium | Content Intelligence Owner | T-Shirt M | EKIE-S3-4 | Approved: rule-based-default parity, 161 pytest green |

### EKIE-S4 Chunking
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S4-1 | Chunking strategies and boundaries | High | Chunking Owner | T-Shirt M | EKIE-S3 Exit | Approved chunking policy |
| EKIE-S4-2 | Token budget and context preservation | High | Chunking Owner | T-Shirt M | EKIE-S4-1 | Token policy approved |
| EKIE-S4-3 | Chunk identity, versioning, lineage | High | Data Governance Owner | T-Shirt M | EKIE-S4-1 | Lineage evidence |
| EKIE-S4-4 | Chunk validation rules | Medium | Quality Lead | T-Shirt S | EKIE-S4-1 | Determinism report |

### EKIE-S5 Embedding
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S5-1 | Provider abstraction and registry | High | ML Platform Owner | T-Shirt M | EKIE-S4 Exit | Approved provider abstraction |
| EKIE-S5-2 | Embedding workflow and batching | High | ML Platform Owner | T-Shirt M | EKIE-S5-1 | Approved workflow |
| EKIE-S5-3 | Embedding versioning and metadata | High | Contract Owner | T-Shirt M | EKIE-S5-2 | Metadata model approved |
| EKIE-S5-4 | Embedding validation | Medium | Quality Lead | T-Shirt S | EKIE-S5-2 | Validation evidence |
| EKIE-S5-5 | Ollama embedding provider (real model) | Medium | ML Platform Owner | T-Shirt M | EKIE-S5-1 | Approved: config-selected provider, 161 pytest green |

### EKIE-S6 Vector Publishing
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S6-1 | Collection schema and payload mapping | High | Contract Owner | T-Shirt M | EKIE-S5 Exit | Required-fields map approved |
| EKIE-S6-2 | Idempotent publish and retry | High | Reliability Owner | T-Shirt M | EKIE-S6-1 | Retry policy sign-off |
| EKIE-S6-3 | Publish verification and lineage closure | High | EKIE Lead | T-Shirt M | EKIE-S6-2 | Verification evidence |
| EKIE-S6-4 | Required-field validation gate | High | Quality Lead | T-Shirt S | EKIE-S6-1 | Validation evidence |
| EKIE-S6-5 | Qdrant vector provider (real DB) | Medium | Reliability Owner | T-Shirt M | EKIE-S6-1 | Approved: config-selected provider, 161 pytest green |

### EKIE-S7 Workflow Orchestration
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S7-1 | Workflow definition and task graph | High | Workflow Owner | T-Shirt M | EKIE-S6 Exit | Approved: typed WorkflowState + pure-function stage graph, 187 pytest green |
| EKIE-S7-2 | Checkpoint and resume recovery | High | Reliability Owner | T-Shirt M | EKIE-S7-1 | Approved: checkpointer + resume, idempotent replay verified |
| EKIE-S7-3 | Dead-letter and retry policy | Medium | Reliability Owner | T-Shirt S | EKIE-S7-1 | Approved: per-stage retry + dead-letter, tested |
| EKIE-S7-4 | Lineage-aware replay and reconciliation | High | Data Governance Owner | T-Shirt M | EKIE-S7-2 | Approved: Control Plane reconciliation replay, tested |

### EKIE-S8 Security And Extensibility
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S8-1 | AuthN, AuthZ, encryption, secrets | High | Security Owner | T-Shirt M | EKIE-S7 Exit | Approved: principal auth + RBAC/ABAC + ephemeral secrets/redaction, 239 pytest green |
| EKIE-S8-2 | Audit logging and policy enforcement | High | Governance Owner | T-Shirt M | EKIE-S8-1 | Approved: append-only audit + per-stage StagePolicyGuard, tested |
| EKIE-S8-3 | Plugin SDK and sandbox validation | Medium | Platform Owner | T-Shirt M | EKIE-S8-1 | Approved: SDK + sandbox + mandatory pre-activation validation gate, tested |
| EKIE-S8-4 | Classification clearance propagation | High | Governance Owner | T-Shirt S | EKIE-S8-1 | Approved: monotonic no-downgrade propagation, tested |

### EKIE-S9 Testing And Deployment Readiness
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| EKIE-S9-1 | Pipeline end-to-end validation suite | High | Quality Lead | T-Shirt L | EKIE-S8 Exit | Approved: PipelineValidator over shared storage, end-to-end no data loss/broken lineage, 252 pytest green |
| EKIE-S9-2 | Data, chunk, embedding, workflow validation | High | Quality Lead | T-Shirt M | EKIE-S9-1 | Approved: per-facet workflow/lineage/chunk/embedding/vector validators, tested |
| EKIE-S9-3 | Load, stress, and failure simulation | Medium | Reliability Owner | T-Shirt M | EKIE-S9-1 | Approved: deterministic load harness (success rate/throughput/p50/p95) + injectable stage failure, tested |
| EKIE-S9-4 | Deployment, HA, and DR readiness | High | DevOps Owner | T-Shirt M | EKIE-S9-1 | Approved: config-driven NFR + RPO/RTO readiness assessment, local-first (no K8s), tested |
| EKIE-S9-5 | EKRE handoff readiness package | High | EKIE Lead | T-Shirt M | EKIE-S9-1, EKIE-S9-4 | Approved: validation-gated HandoffPackage with lineage + geometry proof, tested |

## Track Dependencies
1. Must run after Foundation sprint.
2. EKRE cannot start until EKIE vector publishing and metadata readiness gate passes.

## Track Exit Gate
1. EKIE pipeline, metadata completeness, and deployment readiness gate approved by Product, Architecture, and Quality.

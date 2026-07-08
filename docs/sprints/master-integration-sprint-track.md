# Master Integration Sprint Track

> Track Owner: Program Integration Lead
> Start Condition: Foundation, EKIE, EKRE, and EKCP tracks completed
> Objective: Validate cross-engine integration readiness, resilience, and release governance.
> Source Of Truth: [../master-architecture.md](../master-architecture.md)

## Alignment To Architecture
This track validates the end-to-end system defined in the master architecture: Global Integration Contracts (Section 6), Execution Dependencies and Critical Path (Section 8), and Phase Gates and Success Metrics (Section 9). It exercises the full flow EKIE publish, EKRE retrieval and citation integrity, EKCP orchestration, plus DSAR purge propagation and HTTP 429 backpressure resilience.

## Track Definition Of Ready
1. Foundation, EKIE, EKRE, and EKCP exit gates are approved.
2. Integration evidence handoff from all engine tracks is available.
3. Master sprint owners and review owners are assigned.
4. Go or no-go governance panel is established.

## Track Definition Of Done
1. All master sprint stories meet acceptance criteria with review evidence.
2. Cross-engine compatibility evidence is complete for approved scenarios.
3. Resilience and compliance evidence is approved.
4. Release readiness package is approved by Product, Architecture, and Quality.

## Success Metrics (Track Level)
1. Cross-engine contract compatibility for approved scenarios: 100%.
2. Critical resilience scenario pass rate: 100% for approved scenarios.
3. Compliance scenario pass rate (including purge and policy controls): 100%.
4. Priority sprint commitments delivered: at least 90% by sprint close.

## M1: Cross-Engine Integration Baseline

> Status: Approved (ruff + mypy --strict clean, 9 pytest green). Implemented in the new repo-root `integration/` package: a process-isolated harness (`harness/servers.py`) that launches EKRE and EKCP as independent localhost uvicorn processes (engines share top-level module names and cannot co-exist in one interpreter), a contract compatibility matrix (`matrix/contract_matrix.py`), and live interface tests. Evidence: `integration/evidence/m1_contract_matrix.md`. EKRE runs in its offline deterministic mode (in-memory connector + hash query embedder) for hermetic, fast runs.

### Sprint Objective
Validate baseline integration paths and resolve contract compatibility defects before hardening.

### Scope
1. Contract compatibility checks across all engines.
2. Interface and event-flow validation across boundaries.

### Out Of Scope
1. Engine-internal feature redesign.
2. New feature commitments outside approved sprint scope.

### Stories
1. M1-S1 Contract compatibility matrix and evidence.
2. M1-S2 Service interaction and interface validation.
3. M1-S3 Integration defect triage workflow.

### Deliverables
1. Contract compatibility matrix with status per interface.
2. Interface and event-flow validation report.
3. Integration defect triage and ownership process artifact.

### Acceptance
1. No critical contract mismatches remain unresolved.
2. Cross-engine flow baseline is stable.

### Exit Evidence
1. Signed compatibility matrix and interface validation pack.
2. Approved integration defect disposition log.

### Delivery Evidence
1. M1-S1 Approved: `matrix/contract_matrix.py` builds a compatibility matrix over the shared `packages/contracts` payloads, checking round-trip stability, fork freedom (no engine redefines a contract class locally), and per-engine consumption. `tests/test_m1_contracts.py` asserts zero failures and writes `evidence/m1_contract_matrix.md`. Core retrieval/security contracts (`SecurityContext`, `Citation`, `RetrievalCandidate`, `RetrievalContextPackage`) are PASS and shared EKRE↔EKCP with no forks.
2. M1-S2 Approved: `tests/test_m1_interfaces.py` boots EKRE + EKCP and validates the live boundary — health/readiness on both, EKRE `/v1/query/retrieve` returns a citation package, EKCP `/context/build` (`include_knowledge=true`) reaches EKRE with `degraded=false`, the EKCP gateway bearer-token guard rejects unauthenticated calls (401), and EKRE rejects a tenant/security-context mismatch (403).
3. M1-S3 Approved: integration defect and triage log recorded below.

### Integration Defect & Triage Log (M1-S3)
| ID | Finding | Severity | Disposition |
| --- | --- | --- | --- |
| M1-D1 | `ExecutionContext` contract is defined but not consumed; engines propagate ids via headers + local context objects. | Low (informational) | Accept; revisit if a typed cross-service execution envelope is needed. |
| M1-D2 | `EnterpriseDataPurgeEvent` is defined but there is no cross-service purge propagation mechanism. | Medium | Defer to M2-S2 (DSAR purge propagation). |
| M1-D3 | EKCP gateway auth expects `Authorization: Bearer` / `X-Service-Token`, but `apps/web-ui` sends `X-API-Key`. | Medium | Resolve in M2-S4 (align the web UI to the EKCP gateway token scheme). |
| M1-D4 | EKRE service `.env` selects the HuggingFace query embedder (slow first call); integration runs EKRE in offline hash mode. | Low (env note) | Accept; harness forces `EKRE_WORKERS__QUERY_EMBEDDER=local_hash` for hermetic runs. |

## M2: Resilience, Compliance, and Operational Hardening

> Status: Approved (ruff + mypy --strict clean, integration suite green — 14 pytest across M1+M2). Validated EKCP resilience (backpressure → circuit-open → recovery via a controllable EKRE stub), DSAR purge propagation (`EnterpriseDataPurgeEvent`-driven fan-out to EKCP memory purge), consolidated readiness across all three engines, and a full web UI streaming path (EKCP `/chat/stream` now emits `citation` frames; the web UI now sends the gateway token as `Authorization: Bearer`). Evidence: `integration/evidence/m2_readiness_report.md`.

### Sprint Objective
Validate operational resilience and compliance behavior under constrained and failure conditions.

### Scope
1. Backpressure and circuit-breaking flow validation.
2. DSAR purge propagation validation.
3. Operational readiness and observability checks.

### Out Of Scope
1. Net-new product feature delivery.
2. Non-functional UI cosmetic enhancements beyond integration validation.

### Stories
1. M2-S1 Backpressure and recovery scenario coverage.
2. M2-S2 DSAR purge event propagation checks.
3. M2-S3 SLO/SLA readiness evidence package.
4. M2-S4 Web UI end-to-end integration validation: a complete chat request from `apps/web-ui` through EKCP SSE streaming endpoint through EKRE retrieval through EKCP response returns with streaming tokens and citation cards rendered in the browser. Validate `X-Tenant-ID` and `X-Correlation-ID` are present on every request and correlation IDs appear in EKCP structured logs.

### Deliverables
1. Resilience scenario matrix and results package.
2. DSAR purge propagation evidence report.
3. Operational readiness evidence package for SLO/SLA controls.
4. Web UI end-to-end integration validation evidence (screen recording and network trace).

### Acceptance
1. Resilience behavior matches architecture requirements.
2. Compliance flows pass acceptance checks.
3. End-to-end chat from web UI to EKCP to EKRE and back produces streaming tokens and citation cards with correct tenant and correlation headers.

### Exit Evidence
1. Signed resilience and failure-path validation report.
2. Signed compliance and purge propagation evidence pack.
3. Approved end-to-end web UI integration validation pack (M2-S4).

### Delivery Evidence
1. M2-S1 Approved: `harness/stub_ekre.py` provides a controllable EKRE stand-in (HTTP 429 for N calls, then a valid package). `tests/test_m2_resilience.py` drives EKCP `/context/build` through the full resilience arc — graceful backpressure degradation, an open circuit that sheds load without calling EKRE, and automatic recovery after the reset window (circuit-breaker threshold/reset set via `EKCP_KNOWLEDGE__CIRCUIT_BREAKER_*`).
2. M2-S2 Approved: `harness/purge.py` implements a `PurgeOrchestrator` that fans an `EnterpriseDataPurgeEvent` to per-engine purge adapters. `tests/test_m2_purge.py` seeds EKCP user memory, drives the purge event, and asserts the user's data is hard-deleted and no longer retrievable. Finding: EKIE exposes only per-document delete (no user-scoped DSAR purge); a purge subscriber is the remaining engine work (M2-D1).
3. M2-S3 Approved: `harness/readiness.py` aggregates readiness across EKCP + EKRE (`/v1/readiness`) and EKIE (`/health/ready`) into a consolidated report. `tests/test_m2_readiness.py` asserts all three ready and writes `evidence/m2_readiness_report.md`.
4. M2-S4 Approved: EKCP `services/ekcp/src/api/chat.py` now retrieves enterprise knowledge on `/chat/stream`, emits a `citation` SSE frame per source, and grounds the prompt on the retrieved context (EKCP suite stays green — 186 pytest). `apps/web-ui/lib/api/ekcp.ts` now sends the gateway token as `Authorization: Bearer` (resolving M1-D3). `tests/test_m2_web_ui_e2e.py` drives the exact contract the web UI consumes: it asserts `token`, `citation` (with source path + confidence), and `done` frames, gateway-token enforcement (401 without it), and `X-Correlation-ID` propagation.

### Integration Defect & Triage Log (M2)
| ID | Finding | Severity | Disposition |
| --- | --- | --- | --- |
| M2-D1 | EKIE exposed only per-document delete; no batch DSAR purge surface. | Medium | RESOLVED (post-gate): added EKIE `POST /v1/documents/purge` (batch, tenant-scoped, reuses the deletion service) and registered `ekie_document_purge_adapter` with the `PurgeOrchestrator`. Residual: EKIE has no user attribution (tenant + document scoped), so the subscriber supplies the subject's document set. |
| M2-D2 | Browser-level rendering of the E2E flow is validated at the SSE-contract level (pytest), not via an automated browser. | Low | RESOLVED (post-gate): added a Playwright browser E2E (`apps/web-ui/e2e/chat.spec.ts`) that renders streamed tokens and a citation card in Chromium against the intercepted EKCP SSE contract. |

> Resolved from M1: M1-D3 (web UI auth header) fixed in M2-S4; the EKCP citation-stream gap is closed.

## M3: Go/No-Go and Release Readiness

> Status: Approved (ruff + mypy --strict clean, 16 pytest green across M1+M2+M3). Consolidated the engine + integration evidence, disposed all open risks, and derived the go/no-go decision: **GO** (0 unresolved blocking risks). Evidence: `integration/evidence/m3_release_readiness.md` and `integration/evidence/m3_go_no_go.md`.

### Sprint Objective
Consolidate integration evidence and drive final governance decision for release readiness.

### Scope
1. Final release governance checklist.
2. Risk disposition and escalation readiness.

### Out Of Scope
1. Post-release optimization roadmap.
2. Future backlog reprioritization beyond release gate.

### Stories
1. M3-S1 Final evidence review and sign-off.
2. M3-S2 Open-risk disposition and mitigation acceptance.
3. M3-S3 Go/No-Go decision package.

### Deliverables
1. Consolidated release-readiness evidence package.
2. Open-risk disposition and escalation artifact.
3. Final go or no-go decision package.

### Acceptance
1. Product, Architecture, and Quality sign-offs are complete.
2. Release readiness package is accepted.

### Exit Evidence
1. Signed final release evidence package.
2. Signed go or no-go decision record.

### Delivery Evidence
1. M3-S1 Approved: `release/readiness_package.py` assembles the consolidated release-readiness package (track statuses for Foundation, EKIE, EKRE, EKCP, Web UI, and Master Integration M1/M2). `tests/test_m3_release.py` writes `evidence/m3_release_readiness.md` and asserts every engine and integration track is approved.
2. M3-S2 Approved: the open-risk register (R1-R5) records every finding with a severity, blocking flag, and disposition — including R2 (EKIE user-scoped DSAR purge, medium, non-blocking follow-up) and R4 (Foundation formal exit evidence, low). The M3 test asserts every risk carries a disposition and no unresolved blocking risk remains.
3. M3-S3 Approved: the go/no-go decision is derived from the register (GO when no unresolved blocking risk). Result: **GO**, written to `evidence/m3_go_no_go.md`.

## Risk Register (Track Level)
1. Risk: unresolved integration defects delay release gate.
Mitigation: enforce triage SLA and owner assignment in M1.
2. Risk: resilience scenarios miss critical edge cases.
Mitigation: approve scenario matrix before execution and review gaps at mid-sprint.
3. Risk: incomplete evidence blocks governance sign-off.
Mitigation: require evidence completeness checklist before M3 review.

## Reporting Cadence
1. Weekly integration review with Product, Architecture, and Quality.
2. Mid-sprint blocker review focused on critical-path defects.
3. End-sprint gate review with explicit go or hold decision.

## Sprint Board Backlog (Ready To Use)

### M1 Backlog
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| M1-S1 | Contract compatibility matrix and evidence | High | Integration Architect | T-Shirt M | All engine gates passed | Signed compatibility matrix |
| M1-S2 | Service interaction and interface validation | High | Program Integration Lead | T-Shirt M | M1-S1 | Signed interface validation report |
| M1-S3 | Integration defect triage workflow | Medium | Quality Lead | T-Shirt S | M1-S2 | Approved defect triage log |

### M2 Backlog
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| M2-S1 | Backpressure and recovery scenario coverage | High | Reliability Owner | T-Shirt M | M1 Exit | Signed resilience report |
| M2-S2 | DSAR purge propagation checks | High | Compliance Owner | T-Shirt M | M2-S1 | Signed purge evidence report |
| M2-S3 | SLO/SLA readiness evidence package | Medium | Operations Owner | T-Shirt S | M2-S1 | Signed readiness package |

### M3 Backlog
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| M3-S1 | Final evidence review and sign-off | High | Product Manager | T-Shirt M | M2 Exit | Signed evidence bundle |
| M3-S2 | Open-risk disposition and mitigation acceptance | High | Architecture Owner | T-Shirt S | M3-S1 | Signed risk disposition artifact |
| M3-S3 | Go/No-Go decision package | High | Program Integration Lead | T-Shirt S | M3-S1, M3-S2 | Signed decision record |

## Exit Gate
1. Master release gate accepted.
2. Execution can proceed in release-oriented implementation cadence.

> Master Integration track complete: M1, M2, and M3 approved. Go/No-Go decision: **GO** (0 unresolved blocking risks). All open-risk items are resolved or accepted: R2 (EKIE batch DSAR purge endpoint + orchestrator adapter), R4 (Foundation exit-evidence write-up), R3 (Playwright browser E2E), and R5 (Next.js 16 upgrade, 0 npm audit vulnerabilities). Full integration suite: 16 pytest green, ruff + mypy --strict clean.

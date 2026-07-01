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

## M2: Resilience, Compliance, and Operational Hardening

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

## M3: Go/No-Go and Release Readiness

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

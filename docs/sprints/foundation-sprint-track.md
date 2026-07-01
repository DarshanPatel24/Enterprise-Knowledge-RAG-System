# Foundation Sprint Track

> Track Owner: Product Manager and Architecture Owner
> Status: Mandatory first track
> Objective: Establish shared contracts, governance controls, and blocking quality policies before engine implementation.
> Source Of Truth: [../master-architecture.md](../master-architecture.md)

## Alignment To Architecture
This track operationalizes the Global Enterprise Integration Contracts and Implementation Policy Baseline defined in the master architecture (Sections 6 and 11). It freezes the canonical cross-engine schemas in packages/contracts so EKIE, EKRE, and EKCP consume one authoritative definition without local forks.

## Track Definition Of Ready
1. Master architecture and sprint model are approved.
2. Product, Architecture, and Quality owners are assigned.
3. Contract scope boundaries are agreed for Foundation sprint.
4. Decision log template and review cadence are approved.

## Track Definition Of Done
1. Foundation stories satisfy acceptance criteria with review evidence.
2. Contract ownership map is approved.
3. Governance and quality-gate policy set is approved.
4. EKIE track start gate is approved by Product, Architecture, and Quality.

## Success Metrics (Track Level)
1. Cross-engine contract ownership coverage: 100%.
2. Mandatory baseline contracts approved: 100%.
3. Governance policy approval coverage: 100%.
4. Priority sprint commitments delivered: at least 90% by sprint close.

## Sprint F1: Contracts and Governance Baseline

### Sprint Objective
Lock contract and governance baselines so engine teams can execute with controlled dependencies and blocking quality gates.

### Business Outcome
All engines start from one canonical contract and policy baseline, reducing integration and rework risk.

### In Scope
1. Define canonical schemas in packages/contracts for the global integration contracts:
   1. Vector Database Collection Schema (document_id, chunk_id, tenant_id, classification_clearance, distance_metric).
   2. Security Context (user_id, tenant_id, classification_clearance).
   3. Retrieval Context Package and Citation Payload (source_path, document_id).
   4. Execution Context (request_id, correlation_id, session_id, timestamp).
   5. EnterpriseDataPurgeEvent for GDPR and DSAR propagation.
2. Define contract versioning and deprecation policy (backward compatibility for at least one prior version).
3. Define contract-review workflow and sign-off requirements.
4. Define policy baseline for hardcoding prevention and config-driven values.

### Out Of Scope
1. Engine-specific business logic implementation.
2. UI or external product feature implementation.

### Story Backlog
1. F1-S1 Contract taxonomy and naming standard.
2. F1-S2 Contract schema set v1.0 baseline.
3. F1-S3 Version compatibility and migration policy.
4. F1-S4 Governance checklist and approval workflow.
5. F1-S5 Quality gate policy configuration blueprint.

### Deliverables
1. Contract taxonomy and naming convention artifact.
2. Contract schema baseline package definition.
3. Versioning and compatibility policy document.
4. Governance and approval checklist.
5. Quality gate blueprint for local and CI blocking checks.

### Acceptance Criteria
1. Every cross-engine payload has an approved schema owner.
2. Compatibility rules define backward support expectations.
3. Review workflow captures Product, Architecture, and Quality sign-off.
4. No local schema forks are permitted.

### Exit Evidence
1. Signed contract ownership and taxonomy artifact.
2. Signed compatibility and deprecation policy.
3. Signed governance workflow and quality gate blueprint.

### Dependencies
1. Master architecture baseline must be approved.

### Risks And Mitigation
1. Risk: contract churn from unclear ownership.
2. Mitigation: explicit schema owner map and review gate.

### Exit Gate
1. Foundation gate accepted by Product, Architecture, and Quality.
2. Engine sprint tracks authorized to begin in sequence.

## Risk Register (Track Level)
1. Risk: unclear contract ownership causes decision delays.
Mitigation: assign one owner per schema and require owner sign-off in F1-S2.
2. Risk: policy definitions become non-actionable.
Mitigation: enforce measurable acceptance and blocking gate definitions in F1-S5.
3. Risk: early engine work starts before baseline is stable.
Mitigation: enforce Foundation exit gate as mandatory start condition for EKIE.

## Reporting Cadence
1. Weekly review with Product, Architecture, and Quality.
2. Mid-sprint policy review for unresolved governance items.
3. End-sprint gate review with explicit go or hold decision.

## Sprint Board Backlog (Ready To Use)
| Story ID | Story Name | Priority | Owner | Estimate | Depends On | Done Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| F1-S1 | Contract taxonomy and naming standard | High | Contract PM | T-Shirt S | Master architecture approved | Signed taxonomy artifact |
| F1-S2 | Contract schema set v1.0 baseline | High | Contract Owner | T-Shirt M | F1-S1 | Signed schema baseline package |
| F1-S3 | Version compatibility and migration policy | High | Architecture Owner | T-Shirt M | F1-S2 | Signed compatibility policy |
| F1-S4 | Governance checklist and approval workflow | Medium | Program Governance Lead | T-Shirt S | F1-S1 | Signed governance checklist |
| F1-S5 | Quality gate policy configuration blueprint | High | Quality Lead | T-Shirt M | F1-S3, F1-S4 | Signed quality gate blueprint |

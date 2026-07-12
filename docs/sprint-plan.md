# EK-RAG Sprint Plan (Pre-Execution)

> Version: 2.0
> Status: Approved for Planning, Blocked for Build Until Gates Pass
> Owner: Product Manager
> Scope: Individual sprint tracks per foundation and engine, followed by a separate master integration sprint

## 1. Purpose
This plan defines the official sprint model for EK-RAG delivery. Each feature and engine has its own sprint track for clear ownership and tracking. A separate master sprint track is used only for cross-engine integration and release readiness.

## 2. Sprint Model
1. Foundation Sprint Track (shared contracts and governance)
2. EKIE Sprint Track (ingestion features)
3. EKRE Sprint Track (retrieval features)
4. EKCP Sprint Track (chat orchestration features)
5. Master Sprint Track (cross-engine integration and hardening)

## 3. Sequence And Dependency Rules
1. Foundation sprint must pass before any cross-service implementation.
2. EKIE sprint track starts first after foundation gate.
3. EKRE sprint track starts after EKIE publish and metadata gates pass.
4. EKCP sprint track starts after EKRE citation and security gates pass.
5. Master sprint track starts only after all engine sprint tracks complete.

## 4. Sprint Track Documents
1. Foundation: [sprints/foundation-sprint-track.md](sprints/foundation-sprint-track.md)
2. EKIE: [sprints/ekie-sprint-track.md](sprints/ekie-sprint-track.md)
3. EKRE: [sprints/ekre-sprint-track.md](sprints/ekre-sprint-track.md)
4. EKCP: [sprints/ekcp-sprint-track.md](sprints/ekcp-sprint-track.md)
5. Web UI: [sprints/web-ui-sprint-track.md](sprints/web-ui-sprint-track.md)
6. Master integration: [sprints/master-integration-sprint-track.md](sprints/master-integration-sprint-track.md)

## 5. Required Sprint Metadata (For Every Sprint)
1. Objective and business outcome
2. In-scope and out-of-scope items
3. Story backlog with acceptance criteria
4. Dependency and risk register
5. Test and evidence plan
6. Exit gate and sign-off owners

## 6. Quality Gates (Blocking)
1. Architecture Gate: boundary and ownership compliance
2. Contract Gate: schema versioning and compatibility
3. Security Gate: context propagation and policy enforcement
4. Quality Gate: strict typing, lint, and documentation standards
5. Audit Gate: traceability and evidence completeness

## 7. Governance
1. Product Manager owns prioritization and sprint scope.
2. Architecture Owner owns boundary and contract compliance.
3. Engine Leads own engine-specific decomposition and sequencing.
4. Quality Lead owns acceptance evidence and release-readiness proof.

## 8. Pre-Build Checklist
1. Foundation sprint exit gate accepted
2. Engine sprint track backlog approved
3. Blocking quality gates configured
4. Acceptance criteria baselined for the current sprint
5. Risk mitigations approved for high-severity dependencies

## 9. References
- [master-architecture.md](master-architecture.md)
- [EKIE/EKIE-handbook.md](EKIE/EKIE-handbook.md)
- [EKRE/EKRE-handbook.md](EKRE/EKRE-handbook.md)
- [EKCP/EKCP-handbook.md](EKCP/EKCP-handbook.md)

# EKCP — Enterprise Knowledge Chat Platform

EKCP is the orchestration brain and the only API the Web UI talks to. It owns the
conversation, gates intent, assembles context, commands the LLM, and enforces
governance — routing organizational questions to EKRE and personal questions to
memory, then streaming a governed, cited answer over Server-Sent Events.

## Pipeline
API Gateway (auth + tenant quota) → Conversation Digital Twin + Session → Intent
Gate → Context + Prompt Orchestration → Model Gateway (routing, budget, fallback,
streaming) and Agent Runtime (tools, planning) → Governance PEP (RBAC/ABAC, audit,
PII masking) → SSE stream. Knowledge is fetched from EKRE behind a circuit breaker
with graceful degradation to memory.

## Layout
1. `src/config` — `EkcpSettings` (all `EKCP_*` groups) and `get_settings()`.
2. `src/api` — FastAPI app, guards, and routers (conversation, context, prompt,
   model, memory, agent, governance, workflow, readiness, chat/stream).
3. `src/domain` — orchestration domain logic (intent, conversation, session,
   context, prompt, gateway, memory, tools, planning, agents, governance,
   knowledge, workflow, readiness, integrations, observability, security).
4. `src/composition.py` — the single wiring point (`build_*` factories).
5. `scripts` — `start_api.py` and one offline demo per sprint.
6. `tests` — service tests (ruff + mypy `--strict` clean).

## Quick start
```powershell
# From the repository root, with the venv active.
pip install -e "services/ekcp[dev]"

# Static + test gate
.\.venv\Scripts\python.exe -m ruff check services/ekcp
Push-Location services/ekcp; ..\..\.venv\Scripts\python.exe -m mypy src; Pop-Location
Push-Location services/ekcp; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location

# Run the API (port 8003)
Push-Location services/ekcp; ..\..\.venv\Scripts\python.exe scripts/start_api.py; Pop-Location
```

## Principles
1. Intent-governed routing — personal questions use memory; organizational questions route to EKRE; mixed queries use both.
2. Citation-governed generation — if context cannot be cited, it is not used to generate an answer.
3. No hardcoding — model provider, routing strategy, budgets, and all operational values are configuration-driven.
4. Local-first — deterministic echo provider and in-memory stores are the offline default; real Ollama/HuggingFace models, Redis, and EKRE are config-selected behind lazy seams.
5. Governed & resilient — RBAC/ABAC authorization, audit trails, inbound + outbound PII masking, secret redaction, per-tenant quotas, and circuit-breaker degradation.
6. Streaming UX — real token streaming plus `stage` and `citation` SSE frames so the UI shows live progress and sources.

## Documentation
1. [Deployment Guide](../../docs/EKCP/EKCP-Deployment-Guide.md) — setup, configuration reference, production hardening.
2. [Help Guide](../../docs/EKCP/EKCP-Help_Guide.md) — complete API and domain reference.
3. [Handbook](../../docs/EKCP/EKCP-handbook.md) — architecture and design.
4. [Sprint track](../../docs/sprints/ekcp-sprint-track.md) — delivery history (Phase 0 + S0–S8).

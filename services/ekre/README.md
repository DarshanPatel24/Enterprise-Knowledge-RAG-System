# EKRE — Enterprise Knowledge Retrieval Engine

EKRE transforms a user query into ranked, citation-preserving, policy-compliant
context — the `RetrievalContextPackage` handed to EKCP for response generation.
It reads the vectors EKIE published (inheriting the embedding model and distance
metric); it never ingests, embeds documents, or generates responses.

## Pipeline
Query Intelligence → Execution Core → Retrieval Workers (+ pre-pool security
filter) → Candidate Fusion (RRF) → Ranking → Context Assembly → handoff package,
with cross-cutting tracing, immutable audit, and PII masking.

## Layout
1. `src/config` — `EkreSettings` (all `EKRE_*` groups) and `get_settings()`.
2. `src/api` — FastAPI app, middleware, and routers.
3. `src/domain` — retrieval domain logic (query, execution, connectors, retrieval,
   fusion, ranking, assembly, governance, resilience, evaluation, readiness,
   inheritance, integrations, observability, security).
4. `src/composition.py` — the single wiring point (`build_*` factories).
5. `scripts` — `start_api.py` and one offline demo per sprint.
6. `tests` — service tests (ruff + mypy `--strict` clean).

## Quick start
```powershell
# From the repository root, with the venv active.
pip install -e "services/ekre[dev]"

# Static + test gate
.\.venv\Scripts\python.exe -m ruff check services/ekre
Push-Location services/ekre; ..\..\.venv\Scripts\python.exe -m mypy src; Pop-Location
Push-Location services/ekre; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location

# Run the API (port 8002)
Push-Location services/ekre; ..\..\.venv\Scripts\python.exe scripts/start_api.py; Pop-Location
```

## Principles
1. Deterministic retrieval — same query against the same knowledge state yields identical results.
2. Security before relevance — clearance filtering happens before candidates enter the pool.
3. No hardcoding — embedding model, dimension, and distance metric are inherited from EKIE; all operational values are configuration-driven.
4. Local-first — offline in-memory + deterministic defaults; real Qdrant/model clients are config-selected behind lazy seams.
5. Observability — structured JSON logs with `tenant_id` and `correlation_id`; end-to-end execution trace; self-hosted Langfuse.

## Documentation
1. [Deployment Guide](../../docs/EKRE/EKRE-Deployment-Guide.md) — setup, configuration reference, production hardening.
2. [Help Guide](../../docs/EKRE/EKRE-Help_Guide.md) — complete API and domain reference.
3. [Handbook](../../docs/EKRE/EKRE-handbook.md) — architecture and design.
4. [Sprint track](../../docs/sprints/ekre-sprint-track.md) — delivery history (S0–S8).


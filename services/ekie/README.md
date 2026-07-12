# EKIE — Enterprise Knowledge Ingestion Engine

EKIE is the ingestion factory. It consumes the clean **Markdown** produced by EKDC,
models every document as a versioned **Digital Twin**, then enriches, chunks,
embeds, and publishes governed vectors to Qdrant. It never converts source formats
(EKDC owns that), retrieves, or generates responses.

## Pipeline
Markdown Intake → Document Digital Twin → Intelligence Enrichment → Chunking
(semantic default, recursive optional) → Embedding → Vector Publishing (schema
gate + read-back verification), orchestrated by a resumable, checkpointed workflow
with per-stage security, audit, and lineage tracking.

## Layout
1. `src/config` — `EkieSettings` (all `EKIE_*` groups) and `get_settings()`.
2. `src/api` — FastAPI app, dependencies, and ingestion/repository routers.
3. `src/domain` — ingestion domain logic (sync, transformation, intelligence,
   chunking, embedding, publishing, orchestration, security, plugins, validation,
   storage, control_plane, integrations, observability).
4. `src/composition.py` — the single wiring point (`build_*` factories).
5. `scripts` — `start_api.py`, ingest/sync workers, `deploy.py`/`setup.py`,
   `monitor.py`, and one offline demo per sprint.
6. `tests` — service tests (ruff + mypy `--strict` clean).

## Quick start
```powershell
# From the repository root, with the venv active.
pip install -e "services/ekie[dev]"

# Static + test gate
.\.venv\Scripts\python.exe -m ruff check services/ekie
Push-Location services/ekie; ..\..\.venv\Scripts\python.exe -m mypy src; Pop-Location
Push-Location services/ekie; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location

# Run the API (port 8001)
Push-Location services/ekie; ..\..\.venv\Scripts\python.exe scripts/start_api.py; Pop-Location
```

## Principles
1. Deterministic pipeline — content-hash idempotency means re-runs never duplicate work; the workflow resumes from the last completed stage.
2. Markdown-only intake — EKDC converts every source format upstream; EKIE ingests Markdown (+ txt).
3. No hardcoding — embedding model, dimension, distance metric, and all operational values are configuration-driven.
4. Schema-gated publishing — every Qdrant point carries mandatory governed metadata (`document_id`, `chunk_id`, `tenant_id`, `classification_clearance`, `distance_metric`, `embedding_model`, `embedding_version`, `source_path`, chunk `content`) and is verified by read-back.
5. Local-first — deterministic in-memory/local providers are the offline default; real Qdrant, HuggingFace (`BAAI/bge`), and Ollama clients are config-selected behind lazy seams.
6. Governed — RBAC/ABAC per stage, classification propagation (no silent downgrades), secret redaction, signed plugin sandbox, and a `POST /v1/documents/purge` DSAR path.

## Documentation
1. [Deployment Guide](../../docs/EKIE/EKIE-Deployment-Guide.md) — setup, configuration reference, production hardening.
2. [Help Guide](../../docs/EKIE/EKIE-Help_Guide.md) — complete API and domain reference.
3. [Handbook](../../docs/EKIE/EKIE-handbook.md) — architecture and design.
4. [Sprint track](../../docs/sprints/ekie-sprint-track.md) — delivery history (S0–S9).

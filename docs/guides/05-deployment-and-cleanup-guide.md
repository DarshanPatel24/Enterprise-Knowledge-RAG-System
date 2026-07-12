# EK-RAG Deployment & Cleanup Guide

> Audience: whoever is responsible for taking EK-RAG to a real deployment and for keeping the repository tidy.
> This guide is deliberately blunt about what is production-grade today and what is not.

---

## Part A — Deployment reality: what files exist, and are they best practice?

### A.1 The honest summary

**There is no single, one-command production deployment.** Today an operator:
1. Starts infrastructure with Docker Compose (this part is fine), and
2. **Runs Python "start" scripts by hand, one per engine, in separate terminals.**

The engine start scripts launch a **single-process uvicorn** — a *development* server pattern. There are **no container images (Dockerfiles), no process manager (systemd/supervisor/pm2), no reverse proxy/TLS, and no multi-worker configuration** for the Python services. So yes: **for the engines, you currently "go to the backend file and run it directly" rather than following a proper, packaged deployment procedure.**

The one exception is **EKIE**, which has a genuine, gated deployment/initialization path (`setup.py` + `deploy.py` + defined entry points). **EKRE and EKCP do not have equivalents** — that inconsistency is the single biggest deployment gap.

### A.2 Component-by-component assessment

| Component | File(s) that start it | What it actually does | Best practice? | Gap / what to add |
|---|---|---|---|---|
| **EKIE** | `services/ekie/scripts/start_api.py` (API), `setup.py` (init), `deploy.py` (10-gate), `production_ingest_worker.py`, `production_sync.py`, plus entry points `ekie-api/-setup/-deploy/-worker/-monitor/-purge` | `start_api.py` = single uvicorn process; `setup.py`/`deploy.py` = real initialization + gated validation; workers are real background processors | **Partly.** Init/deploy/workers/entry-points are good practice. The API server itself is still single-process dev-style. | Package the API as a container run under uvicorn/gunicorn **workers**; keep `deploy.py` as the gate. |
| **EKRE** | `services/ekre/scripts/start_api.py` only | Single `uvicorn.run()` on 127.0.0.1:8002 | **No.** Dev-only. | Add a `setup.py`/`deploy.py` parity, a container image, and a worker/health story. |
| **EKCP** | `services/ekcp/scripts/start_api.py` only | Single `uvicorn.run()` on host/port from `.env` | **No.** Dev-only. | Same as EKRE — add init/deploy parity + container + workers. |
| **Web UI** | `apps/web-ui` scripts: `next build` + `next start` | `next start` is a real production server | **Yes (mostly).** | Put behind a reverse proxy/TLS; pin the port (Langfuse owns 3000). No further app change needed. |
| **EKDC** | `services/ekdc/agent.py` | Foreground watcher process; no daemonization | **No (by nature).** Manual foreground. | Wrap in a service manager (systemd/NSSM) or container for unattended operation. |
| **Infrastructure** | `docker-compose.local.yml` | Qdrant, Redis, MinIO, Langfuse (+ its stores) | **Yes, for a single node.** Named "local" for a reason. | For multi-node, move to a managed/orchestrated equivalent; add volumes/backups. |
| **SQL Server** | not in compose (Windows-native) | EKIE control plane | **Environment-specific.** | Fine on Windows; containerize or use managed SQL for portability. |

### A.3 What "files are required" for an actual deployment

At minimum you need, per environment:
- **Infrastructure:** `docker-compose.local.yml` (or a hardened equivalent) + a root `.env` with strong credentials.
- **Per engine:** the engine's `.env` (from its `.env.example`) and the shared Python environment.
- **EKIE only:** run `setup.py` once (schema + bucket), then `start_api.py` + the ingest/sync workers; `deploy.py` to validate.
- **EKRE / EKCP:** their `.env` + `start_api.py` (no init/deploy script exists — this is the gap).
- **Web UI:** `.env.local` + `npm ci && npm run build && npm run start`.
- **EKDC (optional):** its own `.venv`, system tools (Tesseract/FFmpeg/LibreOffice), and `.env`.

### A.4 Recommended production hardening (roadmap)

Priority order:
1. **Containerize each engine** — add a `Dockerfile` per service that runs the API under a production server:
   `uvicorn api.app:app --host 0.0.0.0 --port <p> --workers <N>` (or gunicorn with uvicorn workers). This alone replaces "run the backend script by hand."
2. **Give EKRE and EKCP `setup.py`/`deploy.py` parity** with EKIE and define entry points in their `pyproject.toml` (`ekre-api`, `ekcp-api`, …) so nobody invokes raw script paths.
3. **Add an orchestrator** — a top-level compose (or Kubernetes manifests) that starts infra **and** all engines + Web UI with health checks and restart policies, so it becomes one command.
4. **Reverse proxy + TLS** (nginx/traefik) in front of EKCP and the Web UI; terminate TLS, set security headers, route `/` → Web UI and the API path → EKCP.
5. **Process supervision** for EKDC (systemd unit / Windows service via NSSM / container) so it runs unattended and restarts on failure.
6. **Externalize secrets** (Section B) and remove the committed `.env`.
7. **CI/CD** — build images, run the full test gate (ruff + mypy + pytest + Playwright), and deploy by promoting an image, not by copying source and running scripts.

Until items 1–3 exist, treat the current start scripts as an **evaluation / single-node** deployment, not a hardened production one.

---

## Part B — Configuration for real deployments (dev vs prod)

You have many `.env` files today. That is fine for development. For real deployments, adopt this strategy:

### B.1 Keep the per-service `.env` split, but change *how* values arrive
- **Templates only in git.** Commit `*.env.example`; never commit a filled `.env`. (Today a real root `.env` is committed — remove and rotate it.)
- **One filled config per environment, per service**, generated at deploy time — not hand-edited on the box.
- **Inject secrets from a secrets manager** (Vault, cloud secret store, or your CI's secret store) into the process environment. Pydantic Settings reads OS environment variables directly, so you can supply everything via env vars and skip on-disk `.env` for secrets entirely.
- **Non-secret tunables** (timeouts, limits, feature flags) can stay in a committed, per-environment config overlay.

### B.2 Practical layout
```
config/
  dev/     ekie.env  ekre.env  ekcp.env  web.env    # non-secret defaults per env
  stage/   …
  prod/    …
secrets/   (never in git; supplied by your secret store at deploy time)
```
At deploy: load `config/<env>/<svc>.env` for tunables, then overlay secrets from the vault into the environment, then start the service.

### B.3 Environment parity checklist
- [ ] Same engine versions across dev/stage/prod (pin them).
- [ ] Distinct credentials per environment; least-privilege service accounts.
- [ ] `REQUIRE_GATEWAY_AUTH`, `REQUIRE_SECURITY_CONTEXT`, authorization, masking, audit **all on** in stage/prod.
- [ ] TLS everywhere external; internal engine-to-engine traffic on a private network.
- [ ] Observability (Langfuse + logs) enabled with per-environment keys.

---

## Part C — Repository cleanup

Over development the repo accumulates generated artifacts and dev-only material. Clean it up before archiving, sharing, or building a release image.

### C.1 Cleanup tiers

**Tier 1 — always safe to delete (generated, reproducible).** These are already git-ignored and rebuild automatically:
- Python caches: `__pycache__/`, `*.pyc`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`
- TypeScript/Next build caches: `*.tsbuildinfo`, `apps/web-ui/.next/`, `apps/web-ui/out/`
- Test artifacts: `apps/web-ui/test-results/`, `apps/web-ui/playwright-report/`
- Runtime logs: `*.log` (e.g., `services/ekdc/ekdc_agent.log`)

**Tier 2 — safe but expensive to recreate (delete only to reclaim space / reset):**
- `.venv/` (root and `services/ekdc/.venv/`) — recreate with `pip install`
- `apps/web-ui/node_modules/` — recreate with `npm ci`
- `*.egg-info/` — recreated by `pip install -e` (deleting can temporarily break editable imports until reinstall)

**Tier 3 — user/model data (never delete blindly):**
- `services/ekie/storage/` (assets, HF cache, qdrant data), `services/ekdc/storage/` and `services/ekdc/models/` (Whisper/HF weights) — this is real data and large model caches. Delete only when intentionally resetting an environment.

**Tier 4 — review before removing (source/dev material, may be intentional):**
- Jupyter notebooks: `services/ekdc/document_loaders_handson_participants_copy.ipynb`, `services/ekre/p2_build_rag_with_chunking.ipynb` (training material — keep or move to `docs/training/`).
- Demo scripts: `services/*/scripts/demo_*.py` (teaching examples; keep if referenced by handbooks, otherwise move to an `examples/` folder).
- `services/ekie/code_structure.json` (stale generated analysis — safe to regenerate).
- `docs/EKIE/reviews/` (internal review notes — archive if not referenced).

> **Do not** delete Tier 3/4 automatically. They may be data you need or source someone intends to keep.

### C.2 Cleanup script

A safe, mode-based PowerShell script is provided at the repo root: [`cleanup.ps1`](../../cleanup.ps1).

```powershell
# Preview only (default) — shows what WOULD be removed, deletes nothing:
.\cleanup.ps1

# Actually delete Tier 1 (safe caches, build output, logs):
.\cleanup.ps1 -Apply

# Also remove Tier 2 (node_modules, .venv, egg-info) to fully reset the workspace:
.\cleanup.ps1 -Apply -Deep

# Preview a destructive local DATA reset (wipes Docker volumes; model weights kept):
.\cleanup.ps1 -ResetData

# Execute the data reset (prompts for a typed RESET confirmation):
.\cleanup.ps1 -Apply -ResetData
```

The script **never** touches Tier 3 (data/models) or Tier 4 (notebooks/demos/reviews) during Tier 1/Tier 2 cleanup. After a `-Deep` clean you must reinstall dependencies (`pip install …`, `npm ci`) before running the system again. The optional `-ResetData` tier runs `docker compose -f docker-compose.local.yml down -v` to wipe Qdrant/MinIO/Redis/Langfuse volumes for a clean-slate re-ingest; downloaded model weights are preserved and the SQL Server control plane is not auto-dropped.

### C.3 What to keep

Always keep: all `src/` code, `packages/contracts`, `*.env.example`, `pyproject.toml`/`requirements*.txt`, `package.json`, the `docs/` guides and handbooks, `integration/` tests + evidence, and `docker-compose.local.yml`. These are the product.

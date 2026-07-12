# EK-RAG Admin Guide

> Audience: whoever operates EK-RAG — configuration, security, secrets, data lifecycle, monitoring, backups, and scaling.
> Prerequisite reading: [Help Guide](01-help-guide.md) and [Installation Guide](02-installation-guide.md).

---

## 1. Operational model at a glance

| Component | Process | Port | State it owns | Started by |
|---|---|---|---|---|
| EKIE | Python/FastAPI (uvicorn) | 8001 | SQL Server (control plane) + MinIO (assets) + Qdrant (vectors) | `python services/ekie/scripts/start_api.py` |
| EKRE | Python/FastAPI (uvicorn) | 8002 | none (reads Qdrant) | `python services/ekre/scripts/start_api.py` |
| EKCP | Python/FastAPI (uvicorn) | 8003 | in-memory by default; optional Redis + SQL Server | `python services/ekcp/scripts/start_api.py` |
| Web UI | Next.js | 3001 | browser localStorage only | `npm run start` |
| EKDC | Python watcher | n/a | files on disk + model cache | `python agent.py` |
| Infra | Docker Compose | 6333/6379/9005/3000 | Qdrant/Redis/MinIO/Langfuse | `docker compose -f docker-compose.local.yml up -d` |

The engines are **fully decoupled** — they never share a database and communicate only over REST. The only runtime cross-engine call is **EKCP → EKRE** (`/v1/query/retrieve`).

---

## 2. Configuration model (how settings work)

- Each engine has a **centralized settings module** at `services/<engine>/src/config/settings.py` built on **Pydantic Settings**.
- Every value is **environment-backed** — nothing operational is hardcoded. Defaults live in each `.env.example`.
- **Prefixes** keep engines isolated: `EKIE_`, `EKRE_`, `EKCP_`, plus `EKDC_` and `NEXT_PUBLIC_` (Web UI).
- **Nested settings use a double underscore.** Example: `EKIE_CONTROL_PLANE__HOST` → `settings.control_plane.host`.
- Each engine reads its **own** `.env` (co-located, e.g., `services/ekcp/.env`). The Web UI reads `apps/web-ui/.env.local`.

> To change any tunable, edit the relevant `.env` and restart that service. Never edit code to change an operational value — if a value you need isn't exposed, add it to the settings module and `.env.example` (project rule).

---

## 3. Configuration reference by component

### 3.1 EKIE (`services/ekie/.env`)
| Key group | Purpose |
|---|---|
| `EKIE_CONTROL_PLANE__*` | SQL Server host/instance, `TRUSTED_CONNECTION` (Windows auth) or `USER`/`PASSWORD`. |
| `EKIE_STORAGE__*` | MinIO endpoint, access/secret key, bucket, `SECURE`. |
| `EKIE_QDRANT__*` | Vector DB host/port (must match EKRE). |
| `EKIE_EMBEDDING__*` | `PROVIDER` (`local`/`ollama`/`huggingface`), model, dimension, batching, rate limits. |
| `EKIE_PUBLISHING__*` | `PROVIDER` (`local`/`qdrant`), collection naming. |
| `EKIE_INTELLIGENCE__*` | Optional LLM analysis (off by default), provider/model. |
| `EKIE_CHUNKING__*` | Chunk strategy (`semantic`/`token`/`recursive`) and sizes. |
| `EKIE_SECURITY__*` / `EKIE_GOVERNANCE__*` | Authentication toggle, authorization enforcement, audit, classification downgrade policy. |
| `EKIE_OBSERVABILITY__*` | Langfuse enable/host/keys, log level. |
| `EKIE_DEPLOYMENT__*` | NFR targets used by readiness (success rate, latency, RPO/RTO, replicas). |

### 3.2 EKRE (`services/ekre/.env`)
| Key group | Purpose |
|---|---|
| `EKRE_QDRANT__*` | Vector DB connection (inherits embedding model + distance metric from the collection). |
| `EKRE_WORKERS__*` | `CONNECTOR` (`inmemory`/`qdrant`), `QUERY_EMBEDDER` (`local_hash`/`langchain`), dimension. |
| `EKRE_QUERY__*` | `ENABLE_LLM_INTERPRETER` (off by default) + provider/model. |
| `EKRE_FUSION__*` / `EKRE_RANKING__*` | Fusion identity policy, RRF constant, ranking weights, optional reranker. |
| `EKRE_SECURITY__*` | `REQUIRE_SIGNED_CONTEXT`, `CONTEXT_SIGNING_SECRET`, algorithm. |
| `EKRE_OBSERVABILITY__*` | Langfuse, log level. |

### 3.3 EKCP (`services/ekcp/.env`)
| Key group | Purpose |
|---|---|
| `EKCP_GATEWAY__*` | Host, port (8003), CORS origins, request timeout. |
| `EKCP_SECURITY__*` | **`REQUIRE_GATEWAY_AUTH` + `GATEWAY_AUTH_TOKEN`** (service-to-service bearer), `REQUIRE_SECURITY_CONTEXT`, default clearance. |
| `EKCP_KNOWLEDGE__*` | `ENABLED`, `BASE_URL` (EKRE), timeout, `CIRCUIT_BREAKER_THRESHOLD`/`RESET_SECONDS`, retrieval mode. |
| `EKCP_MODEL__*` | `RUNTIME` (`deterministic`/`langchain`), provider, model, cost/limits. |
| `EKCP_MEMORY__*` | Per-scope TTLs and retrieval weights. |
| `EKCP_GOVERNANCE__*` | `DEFAULT_ROLE`, authorization, audit sink, PII masking toggles. |
| `EKCP_REDIS__*` / `EKCP_CONTROL_PLANE__*` | Optional real session/conversation persistence (default in-memory). |
| `EKCP_OBSERVABILITY__*` | Langfuse, log level. |

### 3.4 Web UI (`apps/web-ui/.env.local`)
| Key | Purpose |
|---|---|
| `NEXT_PUBLIC_EKCP_URL` | EKCP gateway URL (the only backend the UI calls). |
| `NEXT_PUBLIC_EKCP_TENANT_ID` / `USER_ID` / `CLEARANCE` | **Defaults only** — real values are set per-user in the Settings screen and stored in browser localStorage. |

> `NEXT_PUBLIC_` values are compiled into the browser bundle — **never put secrets here.** The gateway token is entered by each user at runtime, not baked in.

### 3.5 EKDC (`services/ekdc/.env`) — full reference
| Variable | Purpose | Default |
|---|---|---|
| `INPUT_DIRECTORY` | Folder to watch for source files | `input_docs` |
| `OUTPUT_DIRECTORY` | Folder for generated Markdown (keep separate from input) | `output_md` |
| `DOCLING_LIBREOFFICE_CMD` | Path to `soffice.exe` for complex DOCX | LibreOffice default path |
| `EKDC_OFFLINE` | Block all remote model downloads (air-gapped) | `false` |
| `EKDC_OCR_ENABLED` | OCR scanned PDFs/images | `true` |
| `EKDC_OCR_ENGINE` | `tesseract`/`tesserocr`/`rapidocr`/`easyocr`/`auto` | `tesseract` |
| `EKDC_OCR_LANGUAGES` | Tesseract language codes (CSV) | `eng` |
| `EKDC_OCR_FORCE_FULL_PAGE` | Force whole-page OCR (image-only PDFs) | `false` |
| `EKDC_TESSERACT_CMD` | Explicit `tesseract.exe` path | unset |
| `EKDC_DOCLING_IMAGE_MODE` | `referenced`/`embedded`/`placeholder` | `referenced` (code) |
| `EKDC_INCLUDE_METADATA` | Prepend YAML front-matter | `true` |
| `EKDC_DESCRIBE_IMAGES` | AI image descriptions (opt-in, needs GPU/model) | `false` |
| `EKDC_VLM_PROVIDER` | `ollama`/`huggingface` | `huggingface` |
| `EKDC_VLM_MODEL` | Vision model id | `Qwen/Qwen2.5-VL-3B-Instruct` |
| `EKDC_VLM_BASE_URL` | Ollama URL | `http://localhost:11434` |
| `EKDC_VLM_MAX_NEW_TOKENS` | Tokens per description | `64` |
| `EKDC_VLM_TRUST_REMOTE_CODE` | Allow model custom code (security) | `false` |
| `EKDC_DEVICE` | `auto`/`cuda`/`cpu` | `auto` |
| `EKDC_MODEL_CACHE_DIR` | Persistent model cache | `./storage` |
| `EKDC_MAX_FILE_SIZE_MB` | DoS guard (0 = unlimited) | `1024` |

---

## 4. Connecting EKDC to EKIE

EKDC produces Markdown; EKIE consumes Markdown. Wire them together:

1. Point EKDC's `OUTPUT_DIRECTORY` at a folder EKIE treats as an ingestion source (an EKIE repository configured for local filesystem sync), **or**
2. Run an ingestion step/worker that reads EKDC's output folder and calls EKIE's ingestion API.

EKIE ships background workers for exactly this: `services/ekie/scripts/production_sync.py` (repository sync) and `services/ekie/scripts/production_ingest_worker.py` (durable ingest job processor). Run them alongside the API for continuous, hands-off ingestion.

> Keep EKDC's input and output folders **separate and non-nested** to avoid conversion feedback loops (EKDC guards against this but warns you).

---

## 5. Security — what to enforce before real use

1. **Gateway authentication (EKCP):** set `EKCP_SECURITY__REQUIRE_GATEWAY_AUTH=true` and a strong `GATEWAY_AUTH_TOKEN`. The Web UI presents it as `Authorization: Bearer <token>`. Without it, `/chat/stream`, `/context/build`, etc. return **401**.
2. **Security context (all engines):** keep `REQUIRE_SECURITY_CONTEXT=true`. Every governed request must carry `{user_id, tenant_id, classification_clearance}`. Tenant mismatches return **403**.
3. **Signed context (EKRE, optional):** enable `EKRE_SECURITY__REQUIRE_SIGNED_CONTEXT` + a signing secret so EKRE trusts only contexts signed by EKCP.
4. **Authorization + roles (EKCP/EKIE):** governance enforces RBAC/ABAC. `EKCP_GOVERNANCE__DEFAULT_ROLE` controls default permissions; use least privilege in production (not blanket `power_user`).
5. **PII masking + audit (EKCP):** masking redacts emails/SSNs/cards/phones from responses; the audit trail records grants/denials/purges. Keep both on.
6. **Classification enforcement:** clearance ordering (`public` < `internal` < `confidential` < `restricted`) filters candidates before ranking; downgrades are blocked by default.
7. **Transport:** the engines serve plain HTTP. For anything beyond a single trusted host, put them behind a **reverse proxy with TLS** (see the [Deployment & Cleanup Guide](05-deployment-and-cleanup-guide.md)).

---

## 6. Secrets management (important)

**Current state:** secrets live in plain `.env` files. There is **no vault/secrets manager**, and a development `.env` containing **real Langfuse keys is currently committed at the repo root**. Representative secret-bearing keys:
- SQL Server: `EKIE_CONTROL_PLANE__PASSWORD`
- MinIO: `EKIE_STORAGE__SECRET_KEY`
- Langfuse: `*_OBSERVABILITY__LANGFUSE_SECRET_KEY`
- EKCP gateway: `EKCP_SECURITY__GATEWAY_AUTH_TOKEN`
- EKRE signing: `EKRE_SECURITY__CONTEXT_SIGNING_SECRET`

**Do this before any real deployment:**
1. **Remove the committed root `.env` from version control** and **rotate every credential** it contained (assume they are compromised).
2. Confirm `.env` files are git-ignored (they are) and keep only `.env.example` templates in the repo.
3. Inject secrets at deploy time via your platform's mechanism (environment variables from a secrets manager / vault / CI secret store), not files on disk where possible.
4. Use distinct credentials per environment (dev/stage/prod) and least-privilege service accounts.

---

## 7. Data lifecycle & DSAR / GDPR purge

EK-RAG supports the "delete a subject's data" (DSAR) flow across engines via the shared `EnterpriseDataPurgeEvent` contract:

- **EKCP memory:** `POST /memory/purge` hard-deletes a user's stored memories for a tenant.
- **EKIE documents:** `POST /v1/documents/purge` batch hard-deletes a supplied set of document IDs for a tenant (reusing the per-document deletion service; idempotent, reports `missing`). *Note:* EKIE data is scoped by **tenant + document** (no per-user attribution), so the DSAR subscriber resolves the subject's document set upstream and passes those IDs.
- **Orchestration:** the integration harness provides a `PurgeOrchestrator` that fans an `EnterpriseDataPurgeEvent` out to both engines' purge endpoints — the pattern a production DSAR subscriber should implement.

**Runbook for a DSAR request:**
1. Identify the subject's tenant, user id, and (for EKIE) their document ids.
2. Call EKCP `/memory/purge` for the user.
3. Call EKIE `/v1/documents/purge` with the document ids.
4. Verify: re-query memory (empty) and confirm the documents/vectors are gone (Qdrant + control plane).
5. Record the purge in your compliance log (EKCP/EKIE audit trails capture the action).

EKIE also provides `services/ekie/scripts/purge_documents.py` (entry point `ekie-purge`) for operational deletes.

---

## 8. Observability & monitoring

- **Langfuse** (`http://localhost:3000`): LLM/agent traces when `*_OBSERVABILITY__LANGFUSE_ENABLED=true` and keys are set. Use it to inspect prompts, retrievals, latencies, and costs.
- **Structured JSON logs:** every engine logs with `tenant_id` and `correlation_id`. Ship these to your log aggregator; filter by `correlation_id` to follow one request across engines.
- **Health/readiness endpoints:**
  - EKIE/EKRE/EKCP: `GET /health/live`; EKRE/EKCP: `GET /v1/readiness`; EKIE: `GET /health/ready`.
  - Use these for uptime checks and load-balancer probes.
- **EKIE monitoring:** `services/ekie/scripts/monitor.py` (entry point `ekie-monitor`) shows per-document stage progress and metrics.

---

## 9. Backups & recovery

Back up the **stateful stores** (the engines themselves are stateless except EKCP's optional Redis/SQL):
| Store | Contains | Backup method |
|---|---|---|
| SQL Server (EKIE control plane) | documents, versions, lineage, jobs | SQL Server backups (full + differential + log) |
| MinIO (`ekie-assets`) | document payloads & intermediate assets | MinIO bucket replication / `mc mirror` |
| Qdrant | published vectors | Qdrant snapshots (volume backup) |
| EKDC model cache | downloaded models | reproducible (re-download) — back up to save time |

**Recovery aids in EKIE:** `recover_lost_payload_docs.py` (payload recovery) and `requeue_jobs.py` (re-drive stuck ingestion jobs).

Set your NFR targets (`EKIE_DEPLOYMENT__RPO_SECONDS`, `RTO_SECONDS`) and validate them with EKIE's readiness assessment.

---

## 10. Scaling & performance

- **EKDC** is CPU/GPU-bound (OCR, transcription, VLM). Give it a GPU (`EKDC_DEVICE=cuda`) for heavy image/audio/video volumes; it runs independently of the engines.
- **EKIE** ingestion is throughput-bound; run multiple `production_ingest_worker.py` workers and tune `EKIE_EMBEDDING__*` batch size and rate limits.
- **EKRE** query latency depends on the embedder + Qdrant. Use a real embedding model matched to the collection; scale Qdrant for large corpora.
- **EKCP** is largely I/O-bound (LLM + EKRE). Its circuit breaker (`EKCP_KNOWLEDGE__CIRCUIT_BREAKER_*`) sheds load when EKRE is saturated (HTTP 429) and degrades gracefully.
- **Multi-tenant limits:** EKCP applies per-tenant concurrency admission; tune `EKCP_DEPLOYMENT__TENANT_MAX_CONCURRENT`.
- **Horizontal scaling caveat:** the engine start scripts run a **single uvicorn process** with no workers. To scale a single engine you must run it under a production server (uvicorn/gunicorn workers) behind a load balancer — see the [Deployment & Cleanup Guide](05-deployment-and-cleanup-guide.md).

---

## 11. Day-2 operations checklist

- [ ] All health/readiness endpoints green.
- [ ] Langfuse receiving traces; logs shipping with `correlation_id`.
- [ ] Gateway auth + security context enforced (401/403 behave as expected).
- [ ] Backups scheduled and test-restored (SQL Server, MinIO, Qdrant).
- [ ] DSAR runbook validated end-to-end.
- [ ] Secrets rotated and out of version control.
- [ ] Ingestion workers healthy; no stuck jobs (`ekie-monitor`).
- [ ] Web UI points at the correct EKCP URL; users can authenticate.

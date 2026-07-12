# Master Integration Harness

Cross-engine validation for EK-RAG. This package is decoupled from the engines:
it starts EKIE, EKRE, and EKCP as independent localhost processes and drives them
over REST, exactly as they communicate in production. No engine source is imported
here (the engines share top-level module names and cannot co-exist in one
interpreter), preserving the decoupling mandated by the architecture.

## Layout
- `harness/servers.py` — subprocess launcher (own `PYTHONPATH`/cwd per engine), health-gated readiness wait, teardown.
- `harness/clients.py` — httpx client injecting `X-Tenant-ID` / `X-Correlation-ID` (and Bearer auth when required).
- `harness/stub_ekre.py` — configurable EKRE stub for resilience/backpressure tests.
- `harness/purge.py` — DSAR purge orchestrator fanning `EnterpriseDataPurgeEvent` to EKCP + EKIE.
- `harness/readiness.py` — aggregates per-engine readiness into an evidence report.
- `matrix/contract_matrix.py` — producer/consumer compatibility checks against `packages/contracts`.
- `release/readiness_package.py` — release readiness + Go/No-Go decision record builder.
- `tests/` — the sprint suites (M1 contracts/interfaces, M2 resilience/purge/readiness/web-ui E2E, M3 release).
- `evidence/` — generated evidence artifacts (contract matrix, readiness, go/no-go).

## Status
M1–M3 complete and approved; release decision is **GO**. See
[master-integration-sprint-track.md](../docs/sprints/master-integration-sprint-track.md).

## Running (from `integration/`)
```
..\.venv\Scripts\python.exe -m ruff check .
..\.venv\Scripts\python.exe -m mypy .
..\.venv\Scripts\python.exe -m pytest
```

## Ports
The harness uses non-standard ports (EKIE 18001, EKRE 18002, EKCP 18003) to avoid
clashing with manually started dev servers on the canonical 8001/8002/8003.

## Local-first
Everything runs on localhost. No containers, no cloud, no external hosts.

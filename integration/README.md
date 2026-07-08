# Master Integration Harness

Cross-engine validation for EK-RAG. This package is decoupled from the engines:
it starts EKIE, EKRE, and EKCP as independent localhost processes and drives them
over REST, exactly as they communicate in production. No engine source is imported
here (the engines share top-level module names and cannot co-exist in one
interpreter), preserving the decoupling mandated by the architecture.

## Layout
- `harness/servers.py` — subprocess launcher (own `PYTHONPATH`/cwd per engine), health-gated readiness wait, teardown.
- `harness/clients.py` — httpx client injecting `X-Tenant-ID` / `X-Correlation-ID`.
- `matrix/contract_matrix.py` — producer/consumer compatibility checks against `packages/contracts`.
- `tests/` — the sprint suites (M1 baseline first).
- `evidence/` — generated evidence artifacts.

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

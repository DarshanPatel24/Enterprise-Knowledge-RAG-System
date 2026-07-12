# EK-RAG Shared Contracts

The single source of truth for every payload that crosses an engine boundary
(EKIE, EKRE, EKCP). All models are Pydantic v2, frozen, and strict (`extra=forbid`);
no service forks these schemas locally.

## Layout
1. `src/contracts` — canonical contract models and the package `__init__` exports.
2. `tests` — contract validation and round-trip/compatibility checks.

## Contracts
| Module | Exports |
|---|---|
| `base.py` | `VersionedContract` (frozen base with `schema_version`) |
| `version.py` | `CONTRACTS_VERSION`, `MIN_SUPPORTED_CONTRACTS_VERSION` |
| `enums.py` | `ClassificationClearance`, `DistanceMetric` |
| `security_context.py` | `SecurityContext` (`user_id`, `tenant_id`, `classification_clearance`) |
| `vector_schema.py` | `VectorCollectionRecord` (governed Qdrant metadata) |
| `retrieval.py` | `Citation`, `RetrievalCandidate`, `RetrievalContextPackage` (EKRE → EKCP handoff) |
| `execution_context.py` | `ExecutionContext` (request/correlation/tenant/session envelope) |
| `events.py` | `EnterpriseDataPurgeEvent` (DSAR fan-out) |

## Quick start
```powershell
# From the repository root, with the venv active.
pip install -e "packages/contracts[dev]"

.\.venv\Scripts\python.exe -m ruff check packages/contracts
Push-Location packages/contracts; ..\..\.venv\Scripts\python.exe -m pytest -q; Pop-Location
```

## Rules
1. One canonical schema definition per payload — no duplication inside service folders.
2. Versioned, backward-compatible evolution; preserve at least one prior version.
3. Breaking changes require architecture approval and a migration plan.
4. All models are Pydantic v2 with strict typing; no service may fork these schemas locally.

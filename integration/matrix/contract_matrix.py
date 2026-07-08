"""Cross-engine contract compatibility matrix.

Validates the shared ``packages/contracts`` payloads without importing any engine
code (the engines share top-level module names and cannot co-exist in one
interpreter). For each contract it checks:

* round-trip stability: a canonical sample validates, dumps, and re-validates;
* fork freedom: no engine redefines a class with the same name locally;
* consumption: which engines reference the contract in their source.

Contracts that are defined but not yet consumed by any engine are reported as
warnings (not failures) so the matrix documents the real integration surface.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from contracts import (
    Citation,
    EnterpriseDataPurgeEvent,
    ExecutionContext,
    RetrievalCandidate,
    RetrievalContextPackage,
    SecurityContext,
    VectorCollectionRecord,
    VersionedContract,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICES: tuple[str, ...] = ("ekie", "ekre", "ekcp")

# Canonical, valid samples for each cross-engine contract.
_CITATION_SAMPLE = {
    "document_id": "doc-1",
    "chunk_id": "chunk-1",
    "source_path": "/enterprise/policy.md",
}
_CANDIDATE_SAMPLE = {
    "citation": _CITATION_SAMPLE,
    "content": "Retention policy is seven years.",
    "relevance_score": 0.92,
    "explanation": "matched policy section",
}

Sample = Mapping[str, object]


@dataclass(frozen=True)
class ContractRow:
    """One row of the compatibility matrix."""

    name: str
    producers: tuple[str, ...]
    consumers: tuple[str, ...]
    roundtrip_ok: bool
    fork_free: bool
    referenced_by: tuple[str, ...]
    status: str
    notes: str


@dataclass(frozen=True)
class _Spec:
    """Declared contract expectations to validate the live matrix against."""

    name: str
    model: type[VersionedContract]
    sample: Sample
    producers: tuple[str, ...]
    consumers: tuple[str, ...]
    note: str = ""


_SPECS: tuple[_Spec, ...] = (
    _Spec(
        "SecurityContext",
        SecurityContext,
        {"user_id": "u-1", "tenant_id": "tenant-a", "classification_clearance": "internal"},
        producers=("ekcp",),
        consumers=("ekre", "ekcp"),
        note="Injected by EKCP, enforced by EKRE ingress.",
    ),
    _Spec(
        "Citation",
        Citation,
        _CITATION_SAMPLE,
        producers=("ekre",),
        consumers=("ekre", "ekcp"),
        note="Produced by EKRE retrieval, consumed by EKCP.",
    ),
    _Spec(
        "RetrievalCandidate",
        RetrievalCandidate,
        _CANDIDATE_SAMPLE,
        producers=("ekre",),
        consumers=("ekre", "ekcp"),
        note="Ranked evidence unit.",
    ),
    _Spec(
        "RetrievalContextPackage",
        RetrievalContextPackage,
        {
            "query": "retention policy",
            "tenant_id": "tenant-a",
            "candidates": [_CANDIDATE_SAMPLE],
            "security_filtered": True,
        },
        producers=("ekre",),
        consumers=("ekcp",),
        note="EKRE -> EKCP retrieval handoff.",
    ),
    _Spec(
        "ExecutionContext",
        ExecutionContext,
        {"request_id": "req-1", "correlation_id": "corr-1", "tenant_id": "tenant-a"},
        producers=(),
        consumers=(),
        note="Defined; engines currently propagate ids via headers/context objects.",
    ),
    _Spec(
        "VectorCollectionRecord",
        VectorCollectionRecord,
        {
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
            "tenant_id": "tenant-a",
            "classification_clearance": "internal",
            "distance_metric": "cosine",
            "source_path": "/enterprise/policy.md",
            "embedding_model": "hash-embedder",
            "embedding_version": 1,
        },
        producers=("ekie",),
        consumers=("ekre",),
        note="Published by EKIE, inherited by EKRE; mirrored structurally today.",
    ),
    _Spec(
        "EnterpriseDataPurgeEvent",
        EnterpriseDataPurgeEvent,
        {"user_id": "u-1", "tenant_id": "tenant-a", "correlation_id": "corr-1"},
        producers=(),
        consumers=(),
        note="Defined; cross-service purge propagation pending (Master Integration M2-S2).",
    ),
)


def _service_python_files(service: str) -> list[Path]:
    src = _REPO_ROOT / "services" / service / "src"
    return list(src.rglob("*.py")) if src.exists() else []


def _references(class_name: str) -> tuple[str, ...]:
    """Return the services whose source references ``class_name`` as a symbol."""
    pattern = re.compile(rf"\b{re.escape(class_name)}\b")
    found: list[str] = []
    for service in SERVICES:
        for path in _service_python_files(service):
            text = path.read_text(encoding="utf-8", errors="replace")
            if pattern.search(text):
                found.append(service)
                break
    return tuple(found)


def _forks(class_name: str) -> tuple[str, ...]:
    """Return the services that locally redefine ``class_name`` (a fork violation)."""
    pattern = re.compile(rf"^\s*class\s+{re.escape(class_name)}\s*\(", re.MULTILINE)
    found: list[str] = []
    for service in SERVICES:
        for path in _service_python_files(service):
            text = path.read_text(encoding="utf-8", errors="replace")
            if pattern.search(text):
                found.append(service)
                break
    return tuple(found)


def _roundtrip_ok(model: type[VersionedContract], sample: Sample) -> bool:
    """Whether a sample validates, dumps, and re-validates without loss."""
    try:
        first = model.model_validate(sample)
        second = model.model_validate(first.model_dump())
    except Exception:
        return False
    return first == second


def _status(spec: _Spec, roundtrip_ok: bool, fork_free: bool, referenced: tuple[str, ...]) -> str:
    if not roundtrip_ok or not fork_free:
        return "fail"
    missing = [consumer for consumer in spec.consumers if consumer not in referenced]
    if missing:
        return "fail"
    if not referenced:
        return "warn"
    return "pass"


def build_matrix() -> list[ContractRow]:
    """Build the full compatibility matrix."""
    rows: list[ContractRow] = []
    for spec in _SPECS:
        roundtrip_ok = _roundtrip_ok(spec.model, spec.sample)
        forks = _forks(spec.name)
        fork_free = len(forks) == 0
        referenced = _references(spec.name)
        status = _status(spec, roundtrip_ok, fork_free, referenced)
        notes = spec.note
        if forks:
            notes = f"FORK in {', '.join(forks)}. {notes}"
        rows.append(
            ContractRow(
                name=spec.name,
                producers=spec.producers,
                consumers=spec.consumers,
                roundtrip_ok=roundtrip_ok,
                fork_free=fork_free,
                referenced_by=referenced,
                status=status,
                notes=notes,
            )
        )
    return rows


def render_markdown(rows: list[ContractRow]) -> str:
    """Render the matrix as a Markdown table for evidence."""
    lines = [
        "# M1-S1 Contract Compatibility Matrix",
        "",
        (
            "| Contract | Producers | Consumers | Round-trip | Fork-free | "
            "Referenced by | Status | Notes |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.name} | {', '.join(row.producers) or '-'} | "
            f"{', '.join(row.consumers) or '-'} | {'yes' if row.roundtrip_ok else 'NO'} | "
            f"{'yes' if row.fork_free else 'NO'} | {', '.join(row.referenced_by) or '-'} | "
            f"{row.status.upper()} | {row.notes} |"
        )
    return "\n".join(lines) + "\n"

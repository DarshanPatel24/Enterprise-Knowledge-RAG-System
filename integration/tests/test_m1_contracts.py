"""M1-S1: cross-engine contract compatibility.

Validates that every shared contract round-trips, is not forked by any engine, and
that the core retrieval/security contracts are consumed by their declared engines.
Writes the compatibility matrix to ``evidence/`` as sprint evidence.
"""

from __future__ import annotations

from pathlib import Path

from matrix.contract_matrix import build_matrix, render_markdown

_EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"

# Contracts that must be actively shared across the live integration surface.
_CORE_CONTRACTS = {
    "SecurityContext",
    "Citation",
    "RetrievalCandidate",
    "RetrievalContextPackage",
}


def test_matrix_has_no_failures_and_writes_evidence() -> None:
    rows = build_matrix()

    _EVIDENCE_DIR.mkdir(exist_ok=True)
    (_EVIDENCE_DIR / "m1_contract_matrix.md").write_text(
        render_markdown(rows), encoding="utf-8"
    )

    failures = [row.name for row in rows if row.status == "fail"]
    assert not failures, f"contract compatibility failures: {failures}"


def test_all_contracts_round_trip_and_are_fork_free() -> None:
    rows = build_matrix()
    for row in rows:
        assert row.roundtrip_ok, f"{row.name} failed round-trip validation"
        assert row.fork_free, f"{row.name} is forked: {row.notes}"


def test_core_contracts_are_consumed_by_declared_engines() -> None:
    rows = {row.name: row for row in build_matrix()}
    for name in _CORE_CONTRACTS:
        row = rows[name]
        assert row.status == "pass", f"{name} is not fully consumed: {row.notes}"
        for consumer in row.consumers:
            assert consumer in row.referenced_by, (
                f"{name} declared consumer {consumer} does not reference it"
            )


def test_retrieval_package_bridges_ekre_to_ekcp() -> None:
    rows = {row.name: row for row in build_matrix()}
    package = rows["RetrievalContextPackage"]
    assert "ekre" in package.referenced_by, "EKRE must produce the retrieval package"
    assert "ekcp" in package.referenced_by, "EKCP must consume the retrieval package"

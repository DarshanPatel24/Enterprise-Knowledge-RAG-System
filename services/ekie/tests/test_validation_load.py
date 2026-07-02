"""Load, throughput, and failure-simulation tests (EKIE-S9-3)."""

from __future__ import annotations

from collections.abc import Callable

from _validation_support import SOURCE, TENANT, build_harness, register_document

from domain.control_plane import ControlPlaneDatabase
from domain.orchestration import StageName
from domain.validation import DocumentLoadSpec, failing_stages, run_load


def _counter_clock() -> Callable[[], float]:
    """Return a deterministic clock incrementing by 1.0 on each call."""
    state = {"t": 0.0}

    def _clock() -> float:
        state["t"] += 1.0
        return state["t"]

    return _clock


def test_run_load_all_succeed(control_plane_db: ControlPlaneDatabase) -> None:
    harness = build_harness(control_plane_db)
    specs = [
        DocumentLoadSpec(
            document_id=register_document(control_plane_db),
            tenant_id=TENANT,
            source_bytes=SOURCE,
        )
        for _ in range(3)
    ]

    report = run_load(harness.orchestrator, specs, clock=_counter_clock())

    assert report.total == 3
    assert report.succeeded == 3
    assert report.dead_lettered == 0
    assert report.success_rate == 1.0
    assert report.p50_seconds == 1.0
    assert report.p95_seconds == 1.0
    assert report.meets_targets(min_success_rate=0.99, max_stage_latency_seconds=5.0)


def test_run_load_dead_letters_on_injected_failure(
    control_plane_db: ControlPlaneDatabase,
) -> None:
    harness = build_harness(
        control_plane_db, stages=failing_stages(StageName.EMBED)
    )
    specs = [
        DocumentLoadSpec(
            document_id=register_document(control_plane_db),
            tenant_id=TENANT,
            source_bytes=SOURCE,
        )
        for _ in range(2)
    ]

    report = run_load(harness.orchestrator, specs, clock=_counter_clock())

    assert report.succeeded == 0
    assert report.dead_lettered == 2
    assert report.success_rate == 0.0
    assert not report.meets_targets(
        min_success_rate=0.99, max_stage_latency_seconds=5.0
    )

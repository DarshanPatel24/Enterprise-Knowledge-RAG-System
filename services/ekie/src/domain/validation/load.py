"""Load, throughput, and latency measurement harness (EKIE-S9-3).

Runs the orchestrator across a batch of documents and aggregates deterministic
non-functional metrics: success rate, throughput, and latency percentiles. The
clock is injectable so tests can assert exact percentile and throughput values
without depending on wall-clock timing.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from domain.orchestration.engine import WorkflowOrchestrator
from domain.orchestration.state import WorkflowStatus


@dataclass(frozen=True)
class DocumentLoadSpec:
    """A single document to drive through the pipeline under load."""

    document_id: str
    tenant_id: str
    source_bytes: bytes
    mime_type: str | None = None


@dataclass(frozen=True)
class LoadReport:
    """Aggregated non-functional metrics for a load run."""

    total: int
    succeeded: int
    dead_lettered: int
    durations_seconds: tuple[float, ...]
    throughput_per_second: float
    p50_seconds: float
    p95_seconds: float
    success_rate: float

    def meets_targets(
        self, *, min_success_rate: float, max_stage_latency_seconds: float
    ) -> bool:
        """Return whether the run meets the configured NFR targets."""
        return (
            self.success_rate >= min_success_rate
            and self.p95_seconds <= max_stage_latency_seconds
        )


def _percentile(values: Sequence[float], percentile: float) -> float:
    """Return the nearest-rank percentile of ``values`` (empty -> 0.0)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = math.ceil(percentile / 100.0 * len(ordered))
    index = min(max(rank - 1, 0), len(ordered) - 1)
    return ordered[index]


def run_load(
    orchestrator: WorkflowOrchestrator,
    documents: Sequence[DocumentLoadSpec],
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> LoadReport:
    """Drive ``documents`` through the orchestrator and aggregate metrics."""
    durations: list[float] = []
    succeeded = 0
    dead_lettered = 0
    wall_start = clock()
    for spec in documents:
        started = clock()
        result = orchestrator.run(
            spec.document_id,
            spec.tenant_id,
            source_bytes=spec.source_bytes,
            mime_type=spec.mime_type,
        )
        durations.append(clock() - started)
        if result.status is WorkflowStatus.COMPLETED:
            succeeded += 1
        elif result.status is WorkflowStatus.DEAD_LETTER:
            dead_lettered += 1
    wall_elapsed = clock() - wall_start

    total = len(documents)
    throughput = total / wall_elapsed if wall_elapsed > 0 else 0.0
    success_rate = succeeded / total if total else 0.0
    return LoadReport(
        total=total,
        succeeded=succeeded,
        dead_lettered=dead_lettered,
        durations_seconds=tuple(durations),
        throughput_per_second=throughput,
        p50_seconds=_percentile(durations, 50.0),
        p95_seconds=_percentile(durations, 95.0),
        success_rate=success_rate,
    )

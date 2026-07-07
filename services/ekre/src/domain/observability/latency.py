"""Stage latency measurement for the retrieval timeline.

Records per-stage durations so every query exposes a latency breakdown and the
stage timeline can be compared against the configured budgets. The recorder is
deterministic under an injected clock, which keeps tests hermetic.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from time import perf_counter

from pydantic import BaseModel, ConfigDict, Field


class LatencyBreakdown(BaseModel):
    """Immutable per-stage latency breakdown for a single retrieval request."""

    model_config = ConfigDict(frozen=True)

    stages: dict[str, float] = Field(default_factory=dict)
    total_ms: float = 0.0

    def over_budget(self, budgets: dict[str, float]) -> dict[str, float]:
        """Return stages whose measured latency exceeds the provided budget."""
        breaches: dict[str, float] = {}
        for stage, elapsed_ms in self.stages.items():
            budget = budgets.get(stage)
            if budget is not None and elapsed_ms > budget:
                breaches[stage] = elapsed_ms
        total_budget = budgets.get("total")
        if total_budget is not None and self.total_ms > total_budget:
            breaches["total"] = self.total_ms
        return breaches


class LatencyRecorder:
    """Accumulate per-stage durations measured via the ``stage`` context manager."""

    def __init__(self, *, clock: Callable[[], float] = perf_counter) -> None:
        self._clock = clock
        self._stages: dict[str, float] = {}

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        """Measure the wall-clock duration of the ``with`` block in milliseconds."""
        start = self._clock()
        try:
            yield
        finally:
            elapsed_ms = (self._clock() - start) * 1000.0
            self._stages[name] = self._stages.get(name, 0.0) + elapsed_ms

    def record(self, name: str, elapsed_ms: float) -> None:
        """Record a pre-measured stage duration in milliseconds."""
        self._stages[name] = self._stages.get(name, 0.0) + elapsed_ms

    def breakdown(self) -> LatencyBreakdown:
        """Return an immutable snapshot of the accumulated stage durations."""
        stages = dict(self._stages)
        total = sum(stages.values())
        return LatencyBreakdown(stages=stages, total_ms=total)

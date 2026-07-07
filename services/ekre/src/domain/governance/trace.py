"""End-to-end execution trace (handbook Chapter 28).

Records the per-stage execution timeline and latency breakdown for a retrieval
request, plus the correlation/trace/execution identifiers. The trace observes
execution; it never influences it.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.observability import LatencyBreakdown


class StageTiming(BaseModel):
    """The measured duration of one pipeline stage."""

    model_config = ConfigDict(frozen=True)

    stage: str = Field(min_length=1)
    duration_ms: float = Field(ge=0.0)


class RetrievalTrace(BaseModel):
    """The immutable execution timeline for one retrieval request."""

    model_config = ConfigDict(frozen=True)

    execution_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    correlation_id: str | None = None
    tenant_id: str = Field(min_length=1)
    stages: tuple[StageTiming, ...] = ()
    total_ms: float = Field(ge=0.0)
    budget_ms: float = Field(ge=0.0)
    over_budget: bool = False
    redactions: int = Field(default=0, ge=0)
    policy_version: str = "v1"


def build_retrieval_trace(
    breakdown: LatencyBreakdown,
    *,
    execution_id: str,
    trace_id: str,
    tenant_id: str,
    budget_ms: float,
    correlation_id: str | None = None,
    redactions: int = 0,
    policy_version: str = "v1",
) -> RetrievalTrace:
    """Build the retrieval trace from a latency breakdown."""
    stages = tuple(
        StageTiming(stage=name, duration_ms=elapsed)
        for name, elapsed in breakdown.stages.items()
    )
    return RetrievalTrace(
        execution_id=execution_id,
        trace_id=trace_id,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        stages=stages,
        total_ms=breakdown.total_ms,
        budget_ms=budget_ms,
        over_budget=breakdown.total_ms > budget_ms,
        redactions=redactions,
        policy_version=policy_version,
    )

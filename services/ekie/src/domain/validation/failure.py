"""Failure-injection helpers for resilience testing (EKIE-S9-3).

Provides pipeline stage sets with a deterministic fault injected at a chosen
stage so tests and demos can exercise the orchestrator's retry and dead-letter
paths without relying on non-deterministic engine failures.
"""

from __future__ import annotations

from domain.orchestration.pipeline import (
    PipelineEngines,
    Stage,
    StageOutcome,
    default_stages,
)
from domain.orchestration.state import StageName, WorkflowState


class InjectedStageFailure(RuntimeError):
    """Deterministic fault raised by an injected failing stage."""

    error_type = "injected_failure"


def failing_stages(fail_at: StageName) -> tuple[Stage, ...]:
    """Return the default stages with ``fail_at`` replaced by a raising stage."""

    def _raise(_engines: PipelineEngines, _state: WorkflowState) -> StageOutcome:
        raise InjectedStageFailure(
            f"injected failure at stage {fail_at.value!r}"
        )

    return tuple(
        Stage(stage.name, _raise) if stage.name is fail_at else stage
        for stage in default_stages()
    )

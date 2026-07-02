"""Unit tests for the orchestration runner, checkpointer, policy, and state."""

from __future__ import annotations

from importlib.util import find_spec
from typing import cast

import pytest

from domain.orchestration import (
    Checkpointer,
    InMemoryCheckpointer,
    LangGraphWorkflowRunner,
    OrchestrationError,
    OrchestrationErrorType,
    OrchestrationEventType,
    OrchestrationPolicy,
    PipelineEngines,
    SequentialWorkflowRunner,
    Stage,
    StageName,
    StageOutcome,
    StageRecord,
    WorkflowState,
    WorkflowStatus,
    runner_from_policy,
)

_ENGINES = cast(PipelineEngines, object())


def _state() -> WorkflowState:
    return WorkflowState(
        document_id="doc-1", tenant_id="tenant-a", correlation_id="corr-1"
    )


def _ok_stage(name: StageName, *, created: bool = True) -> Stage:
    def run(engines: PipelineEngines, state: WorkflowState) -> StageOutcome:
        return StageOutcome(
            asset_id=f"{name.value}-asset",
            version=1,
            content_hash=f"hash-{name.value}",
            created=created,
        )

    return Stage(name, run)


def _flaky_stage(
    name: StageName, *, failures: int, recover: bool
) -> tuple[Stage, dict[str, int]]:
    calls = {"count": 0}

    def run(engines: PipelineEngines, state: WorkflowState) -> StageOutcome:
        calls["count"] += 1
        if calls["count"] <= failures:
            raise RuntimeError(f"transient failure {calls['count']}")
        if not recover:
            raise RuntimeError("permanent failure")
        return StageOutcome(
            asset_id=f"{name.value}-asset",
            version=1,
            content_hash=f"hash-{name.value}",
            created=True,
        )

    return Stage(name, run), calls


class _EventCollector:
    def __init__(self) -> None:
        self.events: list[tuple[OrchestrationEventType, StageName | None]] = []

    def __call__(
        self,
        event_type: OrchestrationEventType,
        stage: StageName | None = None,
        detail: str = "",
    ) -> None:
        self.events.append((event_type, stage))

    def types(self) -> list[OrchestrationEventType]:
        return [event for event, _ in self.events]


def _run(
    runner: SequentialWorkflowRunner,
    state: WorkflowState,
    stages: tuple[Stage, ...],
    *,
    policy: OrchestrationPolicy | None = None,
    checkpointer: Checkpointer | None = None,
    emit: _EventCollector | None = None,
) -> WorkflowState:
    return runner.run(
        state=state,
        engines=_ENGINES,
        stages=stages,
        policy=policy or OrchestrationPolicy(),
        checkpointer=checkpointer or InMemoryCheckpointer(),
        emit=emit or _EventCollector(),
    )


def test_sequential_runner_completes_all_stages() -> None:
    emit = _EventCollector()
    stages = (_ok_stage(StageName.TRANSFORM), _ok_stage(StageName.INTELLIGENCE))
    final = _run(SequentialWorkflowRunner(), _state(), stages, emit=emit)

    assert final.status == WorkflowStatus.COMPLETED
    assert final.completed_stages == (StageName.TRANSFORM, StageName.INTELLIGENCE)
    assert len(final.records) == 2
    assert OrchestrationEventType.WORKFLOW_COMPLETED in emit.types()


def test_sequential_runner_skips_completed_stages_on_resume() -> None:
    emit = _EventCollector()
    prior = _state().with_record(
        StageRecord(
            stage=StageName.TRANSFORM,
            asset_id="a",
            version=1,
            content_hash="h",
            created=True,
        )
    )
    stages = (_ok_stage(StageName.TRANSFORM), _ok_stage(StageName.INTELLIGENCE))
    final = _run(SequentialWorkflowRunner(), prior, stages, emit=emit)

    assert final.status == WorkflowStatus.COMPLETED
    assert (OrchestrationEventType.STAGE_SKIPPED, StageName.TRANSFORM) in emit.events
    assert (OrchestrationEventType.STAGE_COMPLETED, StageName.INTELLIGENCE) in emit.events


def test_sequential_runner_retries_then_succeeds() -> None:
    emit = _EventCollector()
    stage, calls = _flaky_stage(StageName.TRANSFORM, failures=2, recover=True)
    policy = OrchestrationPolicy(max_attempts_per_stage=3, retry_backoff_base_seconds=0.0)
    final = _run(SequentialWorkflowRunner(), _state(), (stage,), policy=policy, emit=emit)

    assert final.status == WorkflowStatus.COMPLETED
    assert calls["count"] == 3
    assert final.records[0].attempts == 3
    assert emit.types().count(OrchestrationEventType.STAGE_RETRIED) == 2


def test_sequential_runner_dead_letters_after_exhausting_retries() -> None:
    emit = _EventCollector()
    failing, _ = _flaky_stage(StageName.INTELLIGENCE, failures=99, recover=False)
    stages = (_ok_stage(StageName.TRANSFORM), failing, _ok_stage(StageName.PUBLISH))
    policy = OrchestrationPolicy(max_attempts_per_stage=2, retry_backoff_base_seconds=0.0)
    final = _run(SequentialWorkflowRunner(), _state(), stages, policy=policy, emit=emit)

    assert final.status == WorkflowStatus.DEAD_LETTER
    assert final.failure is not None
    assert final.failure.stage == StageName.INTELLIGENCE
    assert final.failure.attempts == 2
    assert OrchestrationEventType.WORKFLOW_DEAD_LETTERED in emit.types()
    # The publish stage after the failure must not run.
    assert (OrchestrationEventType.STAGE_STARTED, StageName.PUBLISH) not in emit.events


def test_sequential_runner_checkpoints_final_state() -> None:
    checkpointer = InMemoryCheckpointer()
    stages = (_ok_stage(StageName.TRANSFORM),)
    final = _run(
        SequentialWorkflowRunner(), _state(), stages, checkpointer=checkpointer
    )

    loaded = checkpointer.load("tenant-a", "doc-1")
    assert loaded is not None
    assert loaded.status == final.status == WorkflowStatus.COMPLETED


def test_in_memory_checkpointer_save_load_delete() -> None:
    checkpointer = InMemoryCheckpointer()
    state = _state()
    checkpointer.save(state)
    assert checkpointer.load("tenant-a", "doc-1") == state
    checkpointer.delete("tenant-a", "doc-1")
    assert checkpointer.load("tenant-a", "doc-1") is None


def test_workflow_state_transitions_are_immutable() -> None:
    state = _state()
    record = StageRecord(
        stage=StageName.TRANSFORM,
        asset_id="a",
        version=1,
        content_hash="h",
        created=True,
    )
    updated = state.with_record(record)
    assert state.completed_stages == ()
    assert updated.completed_stages == (StageName.TRANSFORM,)
    assert updated.status == WorkflowStatus.RUNNING
    assert updated.is_complete(StageName.TRANSFORM)


def test_policy_from_settings_maps_fields() -> None:
    class _Settings:
        runner = "langgraph"
        max_attempts_per_stage = 5
        retry_backoff_base_seconds = 0.25
        retry_backoff_multiplier = 3.0
        enable_tracing = True

    policy = OrchestrationPolicy.from_settings(_Settings())
    assert policy.runner == "langgraph"
    assert policy.max_attempts_per_stage == 5
    retry = policy.retry_policy()
    assert retry.max_attempts == 5
    assert retry.backoff_base_seconds == 0.25
    assert retry.backoff_multiplier == 3.0


def test_runner_from_policy_selects_sequential() -> None:
    runner = runner_from_policy(OrchestrationPolicy(runner="sequential"))
    assert isinstance(runner, SequentialWorkflowRunner)


def test_runner_from_policy_rejects_unknown_runner() -> None:
    with pytest.raises(OrchestrationError) as exc:
        runner_from_policy(OrchestrationPolicy(runner="does-not-exist"))
    assert exc.value.error_type == OrchestrationErrorType.RUNNER_UNAVAILABLE


@pytest.mark.skipif(
    find_spec("langgraph") is not None, reason="langgraph is installed"
)
def test_langgraph_runner_unavailable_without_dependency() -> None:
    runner = LangGraphWorkflowRunner()
    with pytest.raises(OrchestrationError) as exc:
        runner.run(
            state=_state(),
            engines=_ENGINES,
            stages=(_ok_stage(StageName.TRANSFORM),),
            policy=OrchestrationPolicy(),
            checkpointer=InMemoryCheckpointer(),
            emit=_EventCollector(),
        )
    assert exc.value.error_type == OrchestrationErrorType.RUNNER_UNAVAILABLE

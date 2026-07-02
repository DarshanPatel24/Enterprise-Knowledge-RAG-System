"""Workflow runners that execute the ingestion stage graph.

Two runners share the same deterministic stage-execution, retry, and
dead-letter semantics:

* :class:`SequentialWorkflowRunner` is the offline default. It walks the stages
  in order, skips already-completed stages on resume, retries transient
  failures, and dead-letters after exhausting attempts.
* :class:`LangGraphWorkflowRunner` builds an equivalent LangGraph ``StateGraph``
  with a checkpointer and optional Langfuse callbacks. It is selected via
  ``EKIE_ORCHESTRATION__RUNNER=langgraph`` and imports ``langgraph`` lazily, so
  the offline path never requires the dependency.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import StrEnum

from domain.orchestration.checkpointer import Checkpointer
from domain.orchestration.errors import OrchestrationError, OrchestrationErrorType
from domain.orchestration.events import EventSink, OrchestrationEventType
from domain.orchestration.pipeline import PipelineEngines, Stage, StageOutcome
from domain.orchestration.policy import OrchestrationPolicy
from domain.orchestration.state import (
    StageFailure,
    StageName,
    StageRecord,
    WorkflowState,
    WorkflowStatus,
)
from domain.sync.retry import RetryPolicy

SleepFn = Callable[[float], None]


def _failure_from(stage: StageName, exc: Exception, attempts: int) -> StageFailure:
    """Build a stage failure, preserving an engine's error-type when present."""
    error_type = getattr(exc, "error_type", None)
    type_str = error_type.value if isinstance(error_type, StrEnum) else "stage_failure"
    return StageFailure(
        stage=stage, error_type=type_str, message=str(exc), attempts=attempts
    )


def _execute_stage_with_retry(
    stage: Stage,
    engines: PipelineEngines,
    state: WorkflowState,
    retry: RetryPolicy,
    sleep: SleepFn,
    emit: EventSink,
) -> tuple[StageOutcome, int]:
    """Run a stage with bounded retries, returning its outcome and attempt count.

    A broad ``Exception`` catch is intentional here: this is the orchestration
    boundary that converts arbitrary engine failures into retry and dead-letter
    signals. The last error is re-raised so the caller can dead-letter it.
    """
    last_error: Exception | None = None
    for attempt in range(retry.max_attempts):
        try:
            return stage.run(engines, state), attempt + 1
        except Exception as exc:  # noqa: BLE001 - DLQ boundary; re-raised below
            last_error = exc
            if attempt == retry.max_attempts - 1:
                break
            emit(
                OrchestrationEventType.STAGE_RETRIED,
                stage.name,
                f"attempt {attempt + 1} failed: {exc}",
            )
            delay = retry.backoff_base_seconds * (retry.backoff_multiplier**attempt)
            if delay > 0:
                sleep(delay)
    assert last_error is not None  # noqa: S101 - loop always sets on failure
    raise last_error


class WorkflowRunner(ABC):
    """Executes the stage graph for a single workflow state."""

    @abstractmethod
    def run(
        self,
        *,
        state: WorkflowState,
        engines: PipelineEngines,
        stages: tuple[Stage, ...],
        policy: OrchestrationPolicy,
        checkpointer: Checkpointer,
        emit: EventSink,
    ) -> WorkflowState:
        """Run the workflow to a terminal state and return the final snapshot."""


class SequentialWorkflowRunner(WorkflowRunner):
    """Deterministic in-process runner; the offline default."""

    def __init__(self, *, sleep: SleepFn = time.sleep) -> None:
        self._sleep = sleep

    def run(
        self,
        *,
        state: WorkflowState,
        engines: PipelineEngines,
        stages: tuple[Stage, ...],
        policy: OrchestrationPolicy,
        checkpointer: Checkpointer,
        emit: EventSink,
    ) -> WorkflowState:
        """Walk stages in order, skipping completed ones and dead-lettering on failure."""
        current = state.marked(WorkflowStatus.RUNNING)
        retry = policy.retry_policy()
        for stage in stages:
            if current.is_complete(stage.name):
                emit(OrchestrationEventType.STAGE_SKIPPED, stage.name, "already complete")
                continue
            emit(OrchestrationEventType.STAGE_STARTED, stage.name)
            try:
                outcome, attempts = _execute_stage_with_retry(
                    stage, engines, current, retry, self._sleep, emit
                )
            except Exception as exc:  # noqa: BLE001 - DLQ boundary
                failure = _failure_from(stage.name, exc, retry.max_attempts)
                current = current.marked(WorkflowStatus.DEAD_LETTER, failure=failure)
                checkpointer.save(current)
                emit(
                    OrchestrationEventType.STAGE_FAILED,
                    stage.name,
                    f"{failure.error_type}: {failure.message}",
                )
                emit(OrchestrationEventType.WORKFLOW_DEAD_LETTERED, stage.name)
                return current
            current = current.with_record(
                StageRecord(
                    stage=stage.name,
                    asset_id=outcome.asset_id,
                    version=outcome.version,
                    content_hash=outcome.content_hash,
                    created=outcome.created,
                    attempts=attempts,
                )
            )
            checkpointer.save(current)
            emit(
                OrchestrationEventType.STAGE_COMPLETED,
                stage.name,
                f"version={outcome.version} created={outcome.created}",
            )
        current = current.marked(WorkflowStatus.COMPLETED)
        checkpointer.save(current)
        emit(OrchestrationEventType.WORKFLOW_COMPLETED)
        return current


class LangGraphWorkflowRunner(WorkflowRunner):
    """LangGraph-backed runner selected when the runtime and package are present.

    Builds a typed ``StateGraph`` whose nodes are the pipeline stages and whose
    edges enforce the deterministic stage order, compiled with a checkpointer
    for resume. Langfuse callbacks and correlation metadata are attached to the
    graph invocation config.
    """

    def __init__(
        self,
        *,
        sleep: SleepFn = time.sleep,
        tracer_callbacks: list[object] | None = None,
    ) -> None:
        self._sleep = sleep
        self._callbacks = tracer_callbacks or []

    def run(
        self,
        *,
        state: WorkflowState,
        engines: PipelineEngines,
        stages: tuple[Stage, ...],
        policy: OrchestrationPolicy,
        checkpointer: Checkpointer,
        emit: EventSink,
    ) -> WorkflowState:
        """Compile and invoke a LangGraph graph mirroring the sequential runner."""
        try:
            from langgraph.checkpoint.memory import MemorySaver
            from langgraph.graph import END, START, StateGraph
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise OrchestrationError(
                OrchestrationErrorType.RUNNER_UNAVAILABLE,
                "langgraph is not installed; set EKIE_ORCHESTRATION__RUNNER=sequential",
            ) from exc

        retry = policy.retry_policy()
        builder: StateGraph = StateGraph(WorkflowState)

        def make_node(stage: Stage) -> Callable[[WorkflowState], WorkflowState]:
            def node(node_state: WorkflowState) -> WorkflowState:
                if node_state.status == WorkflowStatus.DEAD_LETTER:
                    return node_state
                if node_state.is_complete(stage.name):
                    emit(
                        OrchestrationEventType.STAGE_SKIPPED,
                        stage.name,
                        "already complete",
                    )
                    return node_state
                emit(OrchestrationEventType.STAGE_STARTED, stage.name)
                try:
                    outcome, attempts = _execute_stage_with_retry(
                        stage, engines, node_state, retry, self._sleep, emit
                    )
                except Exception as exc:  # noqa: BLE001 - DLQ boundary
                    failure = _failure_from(stage.name, exc, retry.max_attempts)
                    dead = node_state.marked(
                        WorkflowStatus.DEAD_LETTER, failure=failure
                    )
                    checkpointer.save(dead)
                    emit(
                        OrchestrationEventType.STAGE_FAILED,
                        stage.name,
                        f"{failure.error_type}: {failure.message}",
                    )
                    emit(OrchestrationEventType.WORKFLOW_DEAD_LETTERED, stage.name)
                    return dead
                updated = node_state.with_record(
                    StageRecord(
                        stage=stage.name,
                        asset_id=outcome.asset_id,
                        version=outcome.version,
                        content_hash=outcome.content_hash,
                        created=outcome.created,
                        attempts=attempts,
                    )
                )
                checkpointer.save(updated)
                emit(
                    OrchestrationEventType.STAGE_COMPLETED,
                    stage.name,
                    f"version={outcome.version} created={outcome.created}",
                )
                return updated

            return node

        previous = START
        for stage in stages:
            builder.add_node(stage.name.value, make_node(stage))
            builder.add_edge(previous, stage.name.value)
            previous = stage.name.value
        builder.add_edge(previous, END)

        app = builder.compile(checkpointer=MemorySaver())
        config = {
            "configurable": {
                "thread_id": f"{state.tenant_id}:{state.document_id}",
            },
            "callbacks": self._callbacks,
            "metadata": {
                "tenant_id": state.tenant_id,
                "correlation_id": state.correlation_id,
                "session_id": state.document_id,
            },
        }
        result = app.invoke(state.marked(WorkflowStatus.RUNNING), config=config)
        final = WorkflowState.model_validate(result)
        if final.status != WorkflowStatus.DEAD_LETTER:
            final = final.marked(WorkflowStatus.COMPLETED)
            checkpointer.save(final)
            emit(OrchestrationEventType.WORKFLOW_COMPLETED)
        return final


def runner_from_policy(
    policy: OrchestrationPolicy, *, tracer_callbacks: list[object] | None = None
) -> WorkflowRunner:
    """Select a runner from the configured orchestration policy."""
    if policy.runner == "sequential":
        return SequentialWorkflowRunner()
    if policy.runner == "langgraph":
        return LangGraphWorkflowRunner(tracer_callbacks=tracer_callbacks)
    raise OrchestrationError(
        OrchestrationErrorType.RUNNER_UNAVAILABLE,
        f"unknown orchestration runner '{policy.runner}'",
    )

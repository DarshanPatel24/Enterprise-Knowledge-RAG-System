"""Workflow orchestration for the EKIE ingestion pipeline (EKIE-S7).

Orchestrates transform -> intelligence -> chunk -> embed -> publish as a typed,
checkpointed graph with retries, dead-lettering, and lineage-aware replay.
Repository synchronization is the upstream precursor that emits documents into
this pipeline.
"""

from __future__ import annotations

from domain.orchestration.checkpointer import Checkpointer, InMemoryCheckpointer
from domain.orchestration.engine import WorkflowOrchestrator, WorkflowResult
from domain.orchestration.errors import OrchestrationError, OrchestrationErrorType
from domain.orchestration.events import (
    EventSink,
    OrchestrationEvent,
    OrchestrationEventType,
)
from domain.orchestration.pipeline import (
    PipelineEngines,
    Stage,
    StageOutcome,
    default_stages,
)
from domain.orchestration.policy import OrchestrationPolicy, OrchestrationSettingsLike
from domain.orchestration.runner import (
    LangGraphWorkflowRunner,
    SequentialWorkflowRunner,
    WorkflowRunner,
    runner_from_policy,
)
from domain.orchestration.state import (
    StageFailure,
    StageName,
    StageRecord,
    WorkflowState,
    WorkflowStatus,
)
from domain.orchestration.tracing import build_langfuse_callbacks, build_langfuse_client

__all__ = [
    "Checkpointer",
    "EventSink",
    "InMemoryCheckpointer",
    "LangGraphWorkflowRunner",
    "OrchestrationError",
    "OrchestrationErrorType",
    "OrchestrationEvent",
    "OrchestrationEventType",
    "OrchestrationPolicy",
    "OrchestrationSettingsLike",
    "PipelineEngines",
    "SequentialWorkflowRunner",
    "Stage",
    "StageFailure",
    "StageName",
    "StageOutcome",
    "StageRecord",
    "WorkflowOrchestrator",
    "WorkflowResult",
    "WorkflowRunner",
    "WorkflowState",
    "WorkflowStatus",
    "build_langfuse_callbacks",
    "default_stages",
    "runner_from_policy",
]

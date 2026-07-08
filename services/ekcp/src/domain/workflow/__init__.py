"""Workflow and event orchestration domain (handbook Chapter 15)."""

from domain.workflow.engine import WorkflowOrchestrator
from domain.workflow.errors import WorkflowError, WorkflowErrorType
from domain.workflow.events import (
    EventBus,
    InMemoryEventBus,
    LoggingEventBus,
    PlatformEvent,
    PlatformEventType,
    build_platform_event,
)
from domain.workflow.lifecycle import is_allowed, transition
from domain.workflow.models import Workflow, WorkflowState, WorkflowTransition
from domain.workflow.policy import WorkflowPolicy, WorkflowSettingsLike
from domain.workflow.store import InMemoryWorkflowStore, WorkflowStore

__all__ = [
    "EventBus",
    "InMemoryEventBus",
    "InMemoryWorkflowStore",
    "LoggingEventBus",
    "PlatformEvent",
    "PlatformEventType",
    "Workflow",
    "WorkflowError",
    "WorkflowErrorType",
    "WorkflowOrchestrator",
    "WorkflowPolicy",
    "WorkflowSettingsLike",
    "WorkflowState",
    "WorkflowStore",
    "WorkflowTransition",
    "build_platform_event",
    "is_allowed",
    "transition",
]

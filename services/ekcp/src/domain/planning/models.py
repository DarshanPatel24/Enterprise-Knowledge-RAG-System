"""Planning and orchestration models (handbook Chapter 11).

Planning transforms a user objective into an immutable :class:`ExecutionPlan`: an
ordered set of :class:`Task` units with explicit dependencies, an execution
strategy, and human approval gates. Plans are immutable; replanning produces a
new version.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStrategy(StrEnum):
    """How the tasks in a plan are scheduled (handbook 9.10, 11.2)."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"
    EVENT_DRIVEN = "event_driven"


class TaskStatus(StrEnum):
    """Lifecycle status of a task (handbook 11.3)."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task(BaseModel):
    """Immutable smallest schedulable unit of a plan (handbook 11.3)."""

    model_config = ConfigDict(frozen=True)

    task_id: str
    description: str
    required_capability: str
    dependencies: tuple[str, ...] = ()
    expected_outputs: tuple[str, ...] = ()
    priority: int = Field(default=50, ge=0, le=100)
    approval_required: bool = False
    timeout_seconds: float = Field(default=60.0, gt=0.0)
    status: TaskStatus = TaskStatus.PENDING


class ApprovalCheckpoint(BaseModel):
    """Immutable human approval gate within a plan (handbook 11.2)."""

    model_config = ConfigDict(frozen=True)

    checkpoint_id: str
    task_id: str
    required_approvers: tuple[str, ...] = ()


class ExecutionPlan(BaseModel):
    """Immutable execution plan (handbook 11.2)."""

    model_config = ConfigDict(frozen=True)

    plan_id: str
    objective: str
    tasks: tuple[Task, ...] = ()
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    approval_checkpoints: tuple[ApprovalCheckpoint, ...] = ()
    max_tokens: int = 0
    max_cost: float = 0.0
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def task_dependencies(self) -> dict[str, tuple[str, ...]]:
        """Return the dependency map keyed by task id."""
        return {task.task_id: task.dependencies for task in self.tasks}

"""Multi-agent coordination over an execution plan (handbook 9.9, 9.10).

Coordinates the tasks of an execution plan in dependency order: each task selects
an agent by its required capability and runs it, halting at a human approval gate
(governance is a prerequisite, not an afterthought). Coordination is sequential
and deterministic; parallel and event-driven strategies are later enhancements.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from domain.agents.models import (
    AgentOutcome,
    AgentRequest,
    Capability,
)
from domain.agents.policy import AgentPolicy
from domain.agents.registry import AgentRegistry, AgentSelector
from domain.agents.runtime import AgentRuntime
from domain.gateway import LLMGateway
from domain.observability import get_logger
from domain.planning import ExecutionPlan, topological_order
from domain.tools import ToolExecutor

logger = get_logger("ekcp.agents.coordination")


class CoordinationResult(BaseModel):
    """Immutable result of coordinating a plan's tasks."""

    model_config = ConfigDict(frozen=True)

    outcomes: tuple[AgentOutcome, ...] = ()
    completed_tasks: int = 0
    halted_for_approval: bool = False
    halted_task_id: str | None = None
    warnings: tuple[str, ...] = ()


class AgentCoordinator:
    """Coordinate execution plan tasks across capability-selected agents."""

    def __init__(
        self, registry: AgentRegistry, selector: AgentSelector, runtime: AgentRuntime
    ) -> None:
        self._registry = registry
        self._selector = selector
        self._runtime = runtime

    def coordinate(
        self,
        plan: ExecutionPlan,
        *,
        gateway: LLMGateway,
        tool_executor: ToolExecutor,
        policy: AgentPolicy,
        tenant_id: str,
        granted_permissions: frozenset[str] = frozenset(),
    ) -> CoordinationResult:
        """Run the plan's tasks in dependency order, halting at approval gates."""
        outcomes: list[AgentOutcome] = []
        warnings: list[str] = []
        for task in topological_order(plan.tasks):
            if task.approval_required:
                logger.info(
                    "coordination_halted_for_approval",
                    extra={"task_id": task.task_id},
                )
                return CoordinationResult(
                    outcomes=tuple(outcomes),
                    completed_tasks=len(outcomes),
                    halted_for_approval=True,
                    halted_task_id=task.task_id,
                    warnings=tuple(warnings),
                )
            capability = self._resolve_capability(task.required_capability)
            if capability is None:
                warnings.append(
                    f"task {task.task_id}: unknown capability {task.required_capability!r}"
                )
                capability = Capability.REASONING
            request = AgentRequest(
                task_description=task.description,
                capability=capability,
                tenant_id=tenant_id,
                granted_permissions=granted_permissions,
            )
            descriptor = self._selector.select(
                self._registry, capability, granted_permissions=granted_permissions
            )
            outcome = self._runtime.run(
                descriptor,
                request,
                gateway=gateway,
                tool_executor=tool_executor,
                policy=policy,
            )
            outcomes.append(outcome)
        return CoordinationResult(
            outcomes=tuple(outcomes),
            completed_tasks=len(outcomes),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _resolve_capability(value: str) -> Capability | None:
        try:
            return Capability(value)
        except ValueError:
            return None

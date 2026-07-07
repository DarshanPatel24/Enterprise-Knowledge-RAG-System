"""Tests for the agent runtime: selection, execution, tools, coordination."""

from __future__ import annotations

import pytest

from composition import build_model_gateway
from config.settings import AgentSettings, EkcpSettings, ToolSettings
from domain.agents import (
    AgentCoordinator,
    AgentError,
    AgentExecutionStatus,
    AgentPolicy,
    AgentRequest,
    AgentSelector,
    Capability,
    SequentialAgentRunner,
    default_agent_registry,
)
from domain.gateway import LLMGateway
from domain.planning import PlanningEngine, PlanningPolicy
from domain.tools import ToolExecutor, ToolPolicy, default_tool_registry

_RESEARCH_PERMS = frozenset({"tool:knowledge_search"})


def _gateway() -> LLMGateway:
    return build_model_gateway(EkcpSettings(_env_file=None))


def _tool_executor() -> ToolExecutor:
    return ToolExecutor(
        default_tool_registry(), ToolPolicy.from_settings(ToolSettings(_env_file=None))
    )


def _policy(**overrides: object) -> AgentPolicy:
    return AgentPolicy.from_settings(AgentSettings(_env_file=None, **overrides))  # type: ignore[arg-type]


def test_selector_picks_by_capability_not_name() -> None:
    descriptor = AgentSelector().select(
        default_agent_registry(), Capability.REPORTING
    )
    assert descriptor.agent_id == "reporting-agent"


def test_selector_requires_permissions_for_tool_agent() -> None:
    with pytest.raises(AgentError):
        AgentSelector().select(default_agent_registry(), Capability.RESEARCH)
    ok = AgentSelector().select(
        default_agent_registry(), Capability.RESEARCH, granted_permissions=_RESEARCH_PERMS
    )
    assert ok.agent_id == "research-agent"


def test_reasoning_agent_executes_via_gateway() -> None:
    registry = default_agent_registry()
    descriptor = AgentSelector().select(registry, Capability.REASONING)
    outcome = SequentialAgentRunner().run(
        descriptor,
        AgentRequest(
            task_description="Summarize the remote work policy",
            capability=Capability.REASONING,
            tenant_id="tenant-a",
        ),
        gateway=_gateway(),
        tool_executor=_tool_executor(),
        policy=_policy(),
    )
    assert outcome.status is AgentExecutionStatus.COMPLETED
    assert outcome.result
    assert outcome.model_used == "ekcp-echo"
    assert outcome.steps == 1


def test_research_agent_uses_tool() -> None:
    registry = default_agent_registry()
    descriptor = AgentSelector().select(
        registry, Capability.RESEARCH, granted_permissions=_RESEARCH_PERMS
    )
    outcome = SequentialAgentRunner().run(
        descriptor,
        AgentRequest(
            task_description="Find the leave policy",
            capability=Capability.RESEARCH,
            tenant_id="tenant-a",
            granted_permissions=_RESEARCH_PERMS,
        ),
        gateway=_gateway(),
        tool_executor=_tool_executor(),
        policy=_policy(),
    )
    assert outcome.status is AgentExecutionStatus.COMPLETED
    assert len(outcome.tool_usage) == 1
    assert outcome.tool_usage[0].tool_id == "knowledge_search"
    assert outcome.steps == 2


def test_step_budget_bounds_agent_loop() -> None:
    # A research agent needs a tool step + a reasoning step; max_steps=1 truncates.
    registry = default_agent_registry()
    descriptor = AgentSelector().select(
        registry, Capability.RESEARCH, granted_permissions=_RESEARCH_PERMS
    )
    outcome = SequentialAgentRunner().run(
        descriptor,
        AgentRequest(
            task_description="Find the leave policy",
            capability=Capability.RESEARCH,
            tenant_id="tenant-a",
            granted_permissions=_RESEARCH_PERMS,
        ),
        gateway=_gateway(),
        tool_executor=_tool_executor(),
        policy=_policy(max_steps=1),
    )
    assert outcome.status is AgentExecutionStatus.FAILED
    assert outcome.recommended_next_actions


def test_coordinator_runs_plan_and_halts_at_approval() -> None:
    plan = _planning_engine().plan(
        "retrieve data, generate report, obtain approval, notify stakeholders"
    )
    coordinator = AgentCoordinator(
        default_agent_registry(), AgentSelector(), SequentialAgentRunner()
    )
    result = coordinator.coordinate(
        plan,
        gateway=_gateway(),
        tool_executor=_tool_executor(),
        policy=_policy(),
        tenant_id="tenant-a",
    )
    assert result.halted_for_approval is True
    assert result.halted_task_id is not None
    # Tasks before the approval gate ran; the approval task and later ones did not.
    assert result.completed_tasks >= 1


def _planning_engine() -> PlanningEngine:
    from config.settings import PlanningSettings

    return PlanningEngine(PlanningPolicy.from_settings(PlanningSettings(_env_file=None)))

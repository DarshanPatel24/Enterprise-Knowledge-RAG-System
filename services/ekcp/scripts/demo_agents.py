"""Offline demo of the EKCP S5 agent runtime, tools, and planning.

Runs fully offline (no server, no network) using the deterministic model gateway.
Demonstrates a plan decomposition, permission-gated tool execution, capability-
based agent selection and execution, and multi-agent coordination halting at a
human approval gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path so `src/` packages import when run as a script.
_SRC = Path(__file__).resolve().parents[1] / "src"
_CONTRACTS = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "src"
for _path in (_SRC, _CONTRACTS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from composition import (  # noqa: E402
    build_agent_coordinator,
    build_agent_registry,
    build_agent_runtime,
    build_agent_selector,
    build_model_gateway,
    build_planning_engine,
    build_tool_executor,
    configure_observability,
)
from config.settings import AgentSettings, EkcpSettings  # noqa: E402
from domain.agents import AgentPolicy, AgentRequest, Capability  # noqa: E402


def main() -> None:
    """Exercise the S5 agent runtime, tools, and planning, offline."""
    settings = EkcpSettings(_env_file=None)
    configure_observability(settings)
    gateway = build_model_gateway(settings)
    tool_executor = build_tool_executor(settings)
    registry = build_agent_registry(settings)
    selector = build_agent_selector(settings)
    runtime = build_agent_runtime(settings)
    planner = build_planning_engine(settings)
    policy = AgentPolicy.from_settings(AgentSettings(_env_file=None))

    print("--- plan ---")
    plan = planner.plan(
        "retrieve sales data, generate report, obtain approval, notify stakeholders"
    )
    for task in plan.tasks:
        gate = " [approval]" if task.approval_required else ""
        print(f"  {task.task_id}: {task.description} ({task.required_capability}){gate}")

    print("--- research agent (tool-using) ---")
    descriptor = selector.select(
        registry, Capability.RESEARCH, granted_permissions=frozenset({"tool:knowledge_search"})
    )
    outcome = runtime.run(
        descriptor,
        AgentRequest(
            task_description="Find the remote work policy",
            capability=Capability.RESEARCH,
            tenant_id="tenant-a",
            granted_permissions=frozenset({"tool:knowledge_search"}),
        ),
        gateway=gateway,
        tool_executor=tool_executor,
        policy=policy,
    )
    print(f"  agent={outcome.agent_id} status={outcome.status} steps={outcome.steps}")
    print(
        f"  tools={[u.tool_id for u in outcome.tool_usage]} "
        f"confidence={outcome.confidence_score}"
    )
    print(f"  result={outcome.result}")

    print("--- coordination (halts at approval gate) ---")
    coordinator = build_agent_coordinator(settings)
    result = coordinator.coordinate(
        plan,
        gateway=gateway,
        tool_executor=tool_executor,
        policy=policy,
        tenant_id="tenant-a",
    )
    print(
        f"  completed={result.completed_tasks} "
        f"halted_for_approval={result.halted_for_approval} "
        f"halted_task={result.halted_task_id}"
    )


if __name__ == "__main__":
    main()

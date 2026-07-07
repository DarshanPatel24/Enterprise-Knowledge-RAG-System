"""Agent registry and capability-based selection (handbook 9.5, 9.13).

The registry is the authoritative agent catalog. Selection is capability-driven
and permission-aware and never hardcodes an agent by name: the selector returns
the available agent whose capabilities include the requested capability and whose
required permissions the caller holds, preferring the highest quality score.
"""

from __future__ import annotations

from domain.agents.errors import AgentError, AgentErrorType
from domain.agents.models import (
    AgentDescriptor,
    AgentType,
    Capability,
)


class AgentRegistry:
    """Authoritative catalog of registered agents keyed by agent id."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDescriptor] = {}

    def register(self, descriptor: AgentDescriptor) -> None:
        """Register (or replace) an agent descriptor."""
        self._agents[descriptor.agent_id] = descriptor

    def get(self, agent_id: str) -> AgentDescriptor:
        """Return the descriptor for ``agent_id``, or raise ``UNKNOWN_AGENT``."""
        descriptor = self._agents.get(agent_id)
        if descriptor is None:
            raise AgentError(
                AgentErrorType.UNKNOWN_AGENT, f"unknown agent {agent_id!r}"
            )
        return descriptor

    def all(self) -> tuple[AgentDescriptor, ...]:
        """Return every registered agent descriptor."""
        return tuple(self._agents.values())


class AgentSelector:
    """Select an agent by capability, permissions, availability, and quality."""

    def select(
        self,
        registry: AgentRegistry,
        capability: Capability,
        *,
        granted_permissions: frozenset[str] | None = None,
    ) -> AgentDescriptor:
        """Return the best available agent for a capability, or raise NO_AGENT_FOUND."""
        permissions = granted_permissions if granted_permissions is not None else frozenset()
        candidates = [
            agent
            for agent in registry.all()
            if agent.is_available
            and capability in agent.capabilities
            and agent.required_permissions <= permissions
        ]
        if not candidates:
            raise AgentError(
                AgentErrorType.NO_AGENT_FOUND,
                f"no available agent provides capability {capability}",
            )
        candidates.sort(key=lambda a: (-a.quality_score, a.agent_id))
        return candidates[0]


def default_agent_registry() -> AgentRegistry:
    """Return a registry seeded with the deterministic offline sample agents."""
    registry = AgentRegistry()
    registry.register(
        AgentDescriptor(
            agent_id="planner-agent",
            name="Planner Agent",
            agent_type=AgentType.PLANNER,
            capabilities=frozenset({Capability.PLANNING, Capability.REASONING}),
            quality_score=0.8,
        )
    )
    registry.register(
        AgentDescriptor(
            agent_id="research-agent",
            name="Research Agent",
            agent_type=AgentType.SPECIALIST,
            capabilities=frozenset({Capability.RESEARCH, Capability.RETRIEVAL}),
            tool_access=("knowledge_search",),
            required_permissions=frozenset({"tool:knowledge_search"}),
            quality_score=0.85,
        )
    )
    registry.register(
        AgentDescriptor(
            agent_id="analysis-agent",
            name="Analysis Agent",
            agent_type=AgentType.ANALYSIS,
            capabilities=frozenset(
                {Capability.DATA_ANALYSIS, Capability.SUMMARIZATION}
            ),
            quality_score=0.8,
        )
    )
    registry.register(
        AgentDescriptor(
            agent_id="reporting-agent",
            name="Reporting Agent",
            agent_type=AgentType.SPECIALIST,
            capabilities=frozenset({Capability.REPORTING}),
            quality_score=0.75,
        )
    )
    registry.register(
        AgentDescriptor(
            agent_id="validator-agent",
            name="Validator Agent",
            agent_type=AgentType.VALIDATOR,
            capabilities=frozenset({Capability.VALIDATION}),
            quality_score=0.8,
        )
    )
    registry.register(
        AgentDescriptor(
            agent_id="sql-agent",
            name="SQL Agent",
            agent_type=AgentType.TOOL,
            capabilities=frozenset({Capability.SQL_QUERYING}),
            tool_access=("calculator",),
            quality_score=0.75,
        )
    )
    registry.register(
        AgentDescriptor(
            agent_id="workflow-agent",
            name="Workflow Agent",
            agent_type=AgentType.SPECIALIST,
            capabilities=frozenset({Capability.WORKFLOW_EXECUTION}),
            quality_score=0.7,
        )
    )
    registry.register(
        AgentDescriptor(
            agent_id="general-agent",
            name="General Agent",
            agent_type=AgentType.SPECIALIST,
            capabilities=frozenset({Capability.REASONING}),
            quality_score=0.6,
        )
    )
    return registry

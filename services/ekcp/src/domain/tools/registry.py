"""Tool base class, registry, and deterministic sample tools.

A tool is a governed pure-function capability: given a request payload it returns
a result payload with no side effects on the platform. The registry is the
authoritative catalog (no tool executes unless registered) and supports
capability-driven discovery. The sample tools keep the runtime fully offline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.tools.errors import ToolError, ToolErrorType, ToolExecutionFailed
from domain.tools.models import ToolCategory, ToolDescriptor


class Tool(ABC):
    """Abstract governed tool exposing a business capability."""

    @property
    @abstractmethod
    def descriptor(self) -> ToolDescriptor:
        """Return the tool descriptor (identity, capability, permissions)."""

    @abstractmethod
    def execute(self, payload: dict[str, object]) -> dict[str, object]:
        """Execute the tool and return a normalized result payload."""


class ToolRegistry:
    """Authoritative catalog of registered tools with capability discovery."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register (or replace) a tool."""
        self._tools[tool.descriptor.tool_id] = tool

    def get(self, tool_id: str) -> Tool:
        """Return the tool for ``tool_id``, or raise ``UNKNOWN_TOOL``."""
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolError(ToolErrorType.UNKNOWN_TOOL, f"unknown tool {tool_id!r}")
        return tool

    def has(self, tool_id: str) -> bool:
        """Return whether a tool id is registered."""
        return tool_id in self._tools

    def discover(
        self, *, capability: str, granted_permissions: frozenset[str] | None = None
    ) -> list[ToolDescriptor]:
        """Return descriptors matching a capability the caller is permitted to use."""
        permissions = granted_permissions if granted_permissions is not None else frozenset()
        matches: list[ToolDescriptor] = []
        for tool in self._tools.values():
            descriptor = tool.descriptor
            if descriptor.capability != capability:
                continue
            if not descriptor.required_permissions <= permissions:
                continue
            matches.append(descriptor)
        matches.sort(key=lambda d: d.tool_id)
        return matches

    def all(self) -> tuple[ToolDescriptor, ...]:
        """Return every registered tool descriptor."""
        return tuple(tool.descriptor for tool in self._tools.values())


class KnowledgeSearchTool(Tool):
    """Deterministic knowledge-search stub (offline default)."""

    def __init__(self) -> None:
        self._descriptor = ToolDescriptor(
            tool_id="knowledge_search",
            name="Knowledge Search",
            capability="knowledge_search",
            description="Search enterprise knowledge for relevant snippets.",
            category=ToolCategory.INFORMATION_RETRIEVAL,
            required_permissions=frozenset({"tool:knowledge_search"}),
        )

    @property
    def descriptor(self) -> ToolDescriptor:
        return self._descriptor

    def execute(self, payload: dict[str, object]) -> dict[str, object]:
        query = str(payload.get("query", "")).strip()
        if not query:
            raise ToolExecutionFailed("query is required", error_code="missing_query")
        return {
            "query": query,
            "results": [f"reference snippet for '{query}'"],
            "result_count": 1,
        }


class CalculatorTool(Tool):
    """Deterministic arithmetic tool (offline default)."""

    def __init__(self) -> None:
        self._descriptor = ToolDescriptor(
            tool_id="calculator",
            name="Calculator",
            capability="calculation",
            description="Sum a list of numeric operands.",
            category=ToolCategory.UTILITY,
        )

    @property
    def descriptor(self) -> ToolDescriptor:
        return self._descriptor

    def execute(self, payload: dict[str, object]) -> dict[str, object]:
        operands = payload.get("operands", [])
        if not isinstance(operands, list):
            raise ToolExecutionFailed("operands must be a list", error_code="bad_operands")
        try:
            total = sum(float(value) for value in operands)
        except (TypeError, ValueError) as exc:
            raise ToolExecutionFailed(
                "operands must be numeric", error_code="bad_operands"
            ) from exc
        return {"sum": total, "operand_count": len(operands)}


def default_tool_registry() -> ToolRegistry:
    """Return a registry seeded with the deterministic offline sample tools."""
    registry = ToolRegistry()
    registry.register(KnowledgeSearchTool())
    registry.register(CalculatorTool())
    return registry

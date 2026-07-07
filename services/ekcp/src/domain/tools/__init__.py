"""Tool execution platform domain (handbook Chapter 10)."""

from domain.tools.errors import (
    ToolError,
    ToolErrorType,
    ToolExecutionFailed,
)
from domain.tools.executor import ToolExecutor
from domain.tools.models import (
    ToolCategory,
    ToolDescriptor,
    ToolExecutionStatus,
    ToolHealth,
    ToolInvocation,
    ToolRequest,
    ToolResult,
)
from domain.tools.permission import PermissionGate
from domain.tools.policy import ToolPolicy, ToolSettingsLike
from domain.tools.registry import (
    CalculatorTool,
    KnowledgeSearchTool,
    Tool,
    ToolRegistry,
    default_tool_registry,
)

__all__ = [
    "CalculatorTool",
    "KnowledgeSearchTool",
    "PermissionGate",
    "Tool",
    "ToolCategory",
    "ToolDescriptor",
    "ToolError",
    "ToolErrorType",
    "ToolExecutionFailed",
    "ToolExecutionStatus",
    "ToolExecutor",
    "ToolHealth",
    "ToolInvocation",
    "ToolPolicy",
    "ToolRegistry",
    "ToolRequest",
    "ToolResult",
    "ToolSettingsLike",
    "default_tool_registry",
]

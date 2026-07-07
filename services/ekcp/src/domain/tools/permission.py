"""Tool permission gate: authorization before execution (handbook 10.8).

Governance is an execution prerequisite, not a validation step: a tool is only
executed when the caller holds every permission the tool requires. The gate is
pure and deterministic.
"""

from __future__ import annotations

from domain.tools.errors import ToolError, ToolErrorType
from domain.tools.models import ToolDescriptor


class PermissionGate:
    """Authorize tool execution against the caller's granted permissions."""

    def __init__(self, *, enforce: bool = True) -> None:
        self._enforce = enforce

    def authorize(
        self, descriptor: ToolDescriptor, granted_permissions: frozenset[str]
    ) -> None:
        """Raise ``UNAUTHORIZED`` when a required permission is missing."""
        if not self._enforce:
            return
        missing = descriptor.required_permissions - granted_permissions
        if missing:
            raise ToolError(
                ToolErrorType.UNAUTHORIZED,
                (
                    f"tool {descriptor.tool_id!r} requires missing permissions: "
                    f"{', '.join(sorted(missing))}"
                ),
            )

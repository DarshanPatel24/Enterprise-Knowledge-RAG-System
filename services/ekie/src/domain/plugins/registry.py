"""Controlled plugin registry with activation gating (handbook 18.10, ADR-056).

The registry is the control-plane record of installed plugins. A plugin only
becomes active after passing pre-activation validation; execution of an
un-activated plugin is refused. Activation and rejection are auditable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from domain.plugins.errors import PluginError, PluginErrorType
from domain.plugins.sandbox import SandboxExecutor
from domain.plugins.sdk import EKIEPlugin, PluginContext
from domain.plugins.validation import PluginValidator, ValidationReport


class PluginStatus(StrEnum):
    """Lifecycle status of a registered plugin (handbook 18.5)."""

    INSTALLED = "installed"
    ACTIVE = "active"
    REJECTED = "rejected"


@dataclass(frozen=True)
class RegistrationResult:
    """Outcome of attempting to register and activate a plugin."""

    name: str
    status: PluginStatus
    report: ValidationReport


class PluginRegistry:
    """Registers, validates, and activates plugins under least privilege."""

    def __init__(
        self, validator: PluginValidator, sandbox: SandboxExecutor
    ) -> None:
        self._validator = validator
        self._sandbox = sandbox
        self._active: dict[str, EKIEPlugin] = {}
        self._status: dict[str, PluginStatus] = {}

    def register(self, plugin: EKIEPlugin) -> RegistrationResult:
        """Validate ``plugin`` and activate it only when approved."""
        name = plugin.metadata().name
        report = self._validator.validate(plugin)
        if not report.approved:
            self._status[name] = PluginStatus.REJECTED
            return RegistrationResult(
                name=name, status=PluginStatus.REJECTED, report=report
            )
        self._active[name] = plugin
        self._status[name] = PluginStatus.ACTIVE
        return RegistrationResult(
            name=name, status=PluginStatus.ACTIVE, report=report
        )

    def status_of(self, name: str) -> PluginStatus | None:
        """Return the lifecycle status of ``name`` or ``None`` if unknown."""
        return self._status.get(name)

    def is_active(self, name: str) -> bool:
        """Return ``True`` when a plugin named ``name`` is active."""
        return self._status.get(name) is PluginStatus.ACTIVE

    def execute(
        self, name: str, context: PluginContext, input_data: Any  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        """Execute an active plugin inside the sandbox.

        Raises :class:`PluginError` when the plugin is unknown or not active,
        guaranteeing no un-validated plugin ever runs.
        """
        plugin = self._active.get(name)
        if plugin is None:
            error_type = (
                PluginErrorType.NOT_ACTIVATED
                if name in self._status
                else PluginErrorType.UNKNOWN_PLUGIN
            )
            raise PluginError(
                error_type, f"Plugin {name!r} is not active"
            )
        return self._sandbox.run_execute(plugin, context, input_data)

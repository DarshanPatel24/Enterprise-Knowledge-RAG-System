"""Sandboxed plugin execution (handbook 18.8-18.9, ADR-054).

The local-first sandbox runs a plugin's ``validate`` and ``execute`` methods in
isolation from the rest of the engine, converting any raised error into a
:class:`PluginError` so a misbehaving plugin can never crash the pipeline. It
enforces least privilege by construction: the plugin only receives the immutable
:class:`PluginContext` and its declared input, never a database handle or
secret.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from domain.observability import get_logger
from domain.plugins.errors import PluginError, PluginErrorType
from domain.plugins.sdk import EKIEPlugin, PluginContext

_logger = get_logger("ekie.plugins.sandbox")


class SandboxExecutor(ABC):
    """Runs plugin lifecycle methods under isolation and error containment."""

    @abstractmethod
    def run_validate(self, plugin: EKIEPlugin) -> None:
        """Execute ``plugin.validate`` inside the sandbox."""

    @abstractmethod
    def run_execute(
        self, plugin: EKIEPlugin, context: PluginContext, input_data: Any  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        """Initialize and execute ``plugin`` inside the sandbox."""


class InProcessSandbox(SandboxExecutor):
    """Deterministic in-process sandbox with error containment.

    Isolation here is contractual (least-privilege inputs) and defensive (all
    plugin exceptions are contained and translated). Process/container isolation
    (handbook 18.9) plugs in behind this same interface for production.
    """

    def run_validate(self, plugin: EKIEPlugin) -> None:
        """Run ``plugin.validate`` and contain any failure."""
        try:
            plugin.validate()
        except PluginError:
            raise
        except Exception as exc:  # noqa: BLE001 - sandbox containment boundary
            _logger.warning("plugin_validate_failed", extra={"error": str(exc)})
            raise PluginError(
                PluginErrorType.SANDBOX_FAILURE,
                f"Plugin validation raised: {exc}",
            ) from exc

    def run_execute(
        self, plugin: EKIEPlugin, context: PluginContext, input_data: Any  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        """Initialize then execute ``plugin`` with containment."""
        try:
            plugin.initialize(context)
            return plugin.execute(input_data)
        except PluginError:
            raise
        except Exception as exc:  # noqa: BLE001 - sandbox containment boundary
            _logger.warning("plugin_execute_failed", extra={"error": str(exc)})
            raise PluginError(
                PluginErrorType.SANDBOX_FAILURE,
                f"Plugin execution raised: {exc}",
            ) from exc

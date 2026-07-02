"""Plugin interface contract and execution context (handbook 18.6).

Every extension implements :class:`EKIEPlugin`. Plugins are isolated: they
receive an immutable :class:`PluginContext` and must not access the control
plane database directly. The core validates a plugin before it is ever executed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from domain.plugins.manifest import PluginManifest


class PluginContext(BaseModel):
    """Immutable execution context passed to a plugin (handbook 18.6, 18.8).

    Deliberately excludes any database handle or secret material so plugins
    operate under least privilege with controlled inputs only.
    """

    model_config = {"frozen": True}

    tenant_id: str
    correlation_id: str | None = None
    settings: dict[str, str] = Field(default_factory=dict)


class EKIEPlugin(ABC):
    """The plugin interface contract every extension implements (handbook 18.6)."""

    @abstractmethod
    def metadata(self) -> PluginManifest:
        """Return the plugin's declarative manifest."""

    @abstractmethod
    def validate(self) -> None:
        """Perform self-validation; raise on invalid internal state."""

    @abstractmethod
    def initialize(self, context: PluginContext) -> None:
        """Prepare the plugin for execution within ``context``."""

    @abstractmethod
    def execute(self, input_data: Any) -> Any:  # noqa: ANN401
        """Run the plugin's transformation over ``input_data``."""

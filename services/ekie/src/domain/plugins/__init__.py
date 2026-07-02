"""Plugin and extension SDK for EKIE (EKIE-S8, handbook Chapter 18).

Provides the plugin interface contract, manifest and semantic-version
compatibility, a sandbox executor with error containment, mandatory
pre-activation validation, and a controlled registry that activates a plugin
only after it passes validation.
"""

from __future__ import annotations

from domain.plugins.errors import PluginError, PluginErrorType
from domain.plugins.manifest import (
    Compatibility,
    PluginManifest,
    PluginType,
    SemVer,
    compatibility,
)
from domain.plugins.policy import PluginPolicy, PluginSettingsLike
from domain.plugins.registry import (
    PluginRegistry,
    PluginStatus,
    RegistrationResult,
)
from domain.plugins.sandbox import InProcessSandbox, SandboxExecutor
from domain.plugins.sdk import EKIEPlugin, PluginContext
from domain.plugins.validation import (
    CheckStatus,
    PluginValidator,
    ValidationCheck,
    ValidationReport,
)

__all__ = [
    "CheckStatus",
    "Compatibility",
    "EKIEPlugin",
    "InProcessSandbox",
    "PluginContext",
    "PluginError",
    "PluginErrorType",
    "PluginManifest",
    "PluginPolicy",
    "PluginRegistry",
    "PluginSettingsLike",
    "PluginStatus",
    "PluginType",
    "PluginValidator",
    "RegistrationResult",
    "SandboxExecutor",
    "SemVer",
    "ValidationCheck",
    "ValidationReport",
    "compatibility",
]

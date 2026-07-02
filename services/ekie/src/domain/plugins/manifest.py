"""Plugin manifest and semantic version compatibility (handbook 18.7, 18.14).

A manifest declares plugin identity, type, and the EKIE versions it supports.
Compatibility follows semantic versioning: a major-version mismatch blocks
activation, a minor mismatch is allowed with a warning, and a patch mismatch is
always allowed.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel

from domain.plugins.errors import PluginError, PluginErrorType

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class PluginType(StrEnum):
    """Plugin categories supported by the extension SDK (handbook 18.4)."""

    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    PARSER = "parser"
    WORKFLOW = "workflow"
    STORAGE = "storage"
    POLICY = "policy"


class Compatibility(StrEnum):
    """Result of comparing a plugin's target version to the host version."""

    COMPATIBLE = "compatible"
    WARNING = "warning"
    BLOCKED = "blocked"


class SemVer(BaseModel):
    """A parsed MAJOR.MINOR.PATCH semantic version."""

    model_config = {"frozen": True}

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> SemVer:
        """Parse ``value`` as a semantic version or raise :class:`PluginError`."""
        match = _SEMVER_RE.match(value.strip())
        if match is None:
            raise PluginError(
                PluginErrorType.INVALID_MANIFEST,
                f"Invalid semantic version: {value!r}",
            )
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
        )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class PluginManifest(BaseModel):
    """Declarative plugin metadata required for activation (handbook 18.7)."""

    model_config = {"frozen": True}

    name: str
    version: str
    plugin_type: PluginType
    compatible_ekie_versions: str
    author: str
    description: str
    signature: str | None = None


def compatibility(target: str, host: str) -> Compatibility:
    """Return the compatibility class between ``target`` and ``host`` versions."""
    target_version = SemVer.parse(target)
    host_version = SemVer.parse(host)
    if target_version.major != host_version.major:
        return Compatibility.BLOCKED
    if target_version.minor != host_version.minor:
        return Compatibility.WARNING
    return Compatibility.COMPATIBLE

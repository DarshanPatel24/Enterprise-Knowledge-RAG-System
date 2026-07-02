"""Pre-activation plugin validation (handbook 18.13, ADR-054).

No plugin activates without passing every mandatory check: manifest validity,
version compatibility, signature and publisher trust, and a sandboxed
self-validation. Untrusted or failing plugins are rejected.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from domain.plugins.errors import PluginError, PluginErrorType
from domain.plugins.manifest import Compatibility, PluginManifest, SemVer, compatibility
from domain.plugins.policy import PluginPolicy
from domain.plugins.sandbox import SandboxExecutor
from domain.plugins.sdk import EKIEPlugin


class CheckStatus(StrEnum):
    """Outcome of an individual validation check."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ValidationCheck(BaseModel):
    """The result of a single named validation check."""

    model_config = {"frozen": True}

    name: str
    status: CheckStatus
    detail: str = ""


class ValidationReport(BaseModel):
    """Aggregated result of all pre-activation checks for a plugin."""

    model_config = {"frozen": True}

    plugin_name: str
    approved: bool
    checks: tuple[ValidationCheck, ...]

    @property
    def failures(self) -> tuple[ValidationCheck, ...]:
        """Return the checks that failed."""
        return tuple(c for c in self.checks if c.status is CheckStatus.FAILED)


class PluginValidator:
    """Runs the mandatory pre-activation checks for a plugin (handbook 18.13)."""

    def __init__(self, policy: PluginPolicy, sandbox: SandboxExecutor) -> None:
        self._policy = policy
        self._sandbox = sandbox

    def validate(self, plugin: EKIEPlugin) -> ValidationReport:
        """Run all checks and return an aggregated :class:`ValidationReport`."""
        manifest = plugin.metadata()
        checks: list[ValidationCheck] = [
            self._check_manifest(manifest),
            self._check_compatibility(manifest),
            self._check_signature(manifest),
            self._check_sandbox(plugin),
        ]
        approved = all(c.status is not CheckStatus.FAILED for c in checks)
        return ValidationReport(
            plugin_name=manifest.name, approved=approved, checks=tuple(checks)
        )

    def validate_for_activation(self, plugin: EKIEPlugin) -> ValidationReport:
        """Validate and raise :class:`PluginError` when not approved."""
        report = self.validate(plugin)
        if not report.approved:
            reasons = "; ".join(
                f"{c.name}:{c.detail}" for c in report.failures
            )
            raise PluginError(
                PluginErrorType.VALIDATION_FAILED,
                f"Plugin {report.plugin_name!r} failed validation: {reasons}",
            )
        return report

    def _check_manifest(self, manifest: PluginManifest) -> ValidationCheck:
        """Verify required manifest identity fields are present and valid."""
        if not manifest.name or not manifest.author:
            return ValidationCheck(
                name="manifest",
                status=CheckStatus.FAILED,
                detail="name and author are required",
            )
        try:
            SemVer.parse(manifest.version)
        except PluginError:
            return ValidationCheck(
                name="manifest",
                status=CheckStatus.FAILED,
                detail=f"invalid version {manifest.version!r}",
            )
        return ValidationCheck(name="manifest", status=CheckStatus.PASSED)

    def _check_compatibility(self, manifest: PluginManifest) -> ValidationCheck:
        """Enforce semantic-version compatibility with the host engine."""
        try:
            result = compatibility(
                manifest.compatible_ekie_versions, self._policy.ekie_version
            )
        except PluginError as exc:
            return ValidationCheck(
                name="compatibility", status=CheckStatus.FAILED, detail=str(exc)
            )
        if result is Compatibility.BLOCKED:
            return ValidationCheck(
                name="compatibility",
                status=CheckStatus.FAILED,
                detail="major version mismatch",
            )
        if result is Compatibility.WARNING:
            return ValidationCheck(
                name="compatibility",
                status=CheckStatus.WARNING,
                detail="minor version mismatch",
            )
        return ValidationCheck(name="compatibility", status=CheckStatus.PASSED)

    def _check_signature(self, manifest: PluginManifest) -> ValidationCheck:
        """Verify signature presence and publisher trust per policy."""
        if manifest.signature is None:
            if self._policy.allow_unsigned or not self._policy.require_signature:
                return ValidationCheck(
                    name="signature",
                    status=CheckStatus.WARNING,
                    detail="unsigned plugin permitted by policy",
                )
            return ValidationCheck(
                name="signature",
                status=CheckStatus.FAILED,
                detail="signature required but absent",
            )
        trusted = self._policy.trusted_publishers
        if trusted and manifest.author not in trusted:
            return ValidationCheck(
                name="signature",
                status=CheckStatus.FAILED,
                detail=f"publisher {manifest.author!r} is not trusted",
            )
        return ValidationCheck(name="signature", status=CheckStatus.PASSED)

    def _check_sandbox(self, plugin: EKIEPlugin) -> ValidationCheck:
        """Run the plugin's self-validation inside the sandbox."""
        try:
            self._sandbox.run_validate(plugin)
        except PluginError as exc:
            return ValidationCheck(
                name="sandbox", status=CheckStatus.FAILED, detail=str(exc)
            )
        return ValidationCheck(name="sandbox", status=CheckStatus.PASSED)

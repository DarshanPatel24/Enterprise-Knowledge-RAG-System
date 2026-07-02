"""Tests for the plugin SDK and sandbox validation (EKIE-S8)."""

from __future__ import annotations

from typing import Any

import pytest

from config.settings import PluginSettings
from domain.plugins import (
    CheckStatus,
    Compatibility,
    EKIEPlugin,
    InProcessSandbox,
    PluginContext,
    PluginError,
    PluginErrorType,
    PluginManifest,
    PluginPolicy,
    PluginRegistry,
    PluginStatus,
    PluginType,
    PluginValidator,
    SemVer,
    compatibility,
)


class _EchoPlugin(EKIEPlugin):
    """A minimal well-behaved plugin used across the tests."""

    def __init__(
        self,
        *,
        name: str = "echo",
        version: str = "1.0.0",
        compatible: str = "1.0.0",
        author: str = "acme",
        signature: str | None = "sig",
    ) -> None:
        self._manifest = PluginManifest(
            name=name,
            version=version,
            plugin_type=PluginType.PARSER,
            compatible_ekie_versions=compatible,
            author=author,
            description="echo plugin",
            signature=signature,
        )

    def metadata(self) -> PluginManifest:
        return self._manifest

    def validate(self) -> None:
        return None

    def initialize(self, context: PluginContext) -> None:
        return None

    def execute(self, input_data: Any) -> Any:
        return input_data


class _BrokenValidatePlugin(_EchoPlugin):
    def validate(self) -> None:
        raise ValueError("bad internal state")


class _BrokenExecutePlugin(_EchoPlugin):
    def execute(self, input_data: Any) -> Any:
        raise RuntimeError("boom")


def _policy(**overrides: object) -> PluginPolicy:
    return PluginPolicy(**overrides)  # type: ignore[arg-type]


def _validator(policy: PluginPolicy | None = None) -> PluginValidator:
    return PluginValidator(policy or _policy(), InProcessSandbox())


# --- Semantic version and compatibility (18.14) ------------------------------


def test_semver_parses_valid_version() -> None:
    version = SemVer.parse("2.3.4")
    assert (version.major, version.minor, version.patch) == (2, 3, 4)
    assert str(version) == "2.3.4"


def test_semver_rejects_invalid_version() -> None:
    with pytest.raises(PluginError) as exc:
        SemVer.parse("1.2")
    assert exc.value.error_type is PluginErrorType.INVALID_MANIFEST


@pytest.mark.parametrize(
    ("target", "host", "expected"),
    [
        ("1.0.0", "1.0.5", Compatibility.COMPATIBLE),
        ("1.2.0", "1.3.0", Compatibility.WARNING),
        ("2.0.0", "1.0.0", Compatibility.BLOCKED),
    ],
)
def test_compatibility_classes(
    target: str, host: str, expected: Compatibility
) -> None:
    assert compatibility(target, host) is expected


# --- Sandbox containment (18.8) ----------------------------------------------


def test_sandbox_contains_validate_failure() -> None:
    with pytest.raises(PluginError) as exc:
        InProcessSandbox().run_validate(_BrokenValidatePlugin())
    assert exc.value.error_type is PluginErrorType.SANDBOX_FAILURE


def test_sandbox_contains_execute_failure() -> None:
    sandbox = InProcessSandbox()
    context = PluginContext(tenant_id="t1")
    with pytest.raises(PluginError) as exc:
        sandbox.run_execute(_BrokenExecutePlugin(), context, "x")
    assert exc.value.error_type is PluginErrorType.SANDBOX_FAILURE


def test_sandbox_executes_healthy_plugin() -> None:
    sandbox = InProcessSandbox()
    context = PluginContext(tenant_id="t1")
    assert sandbox.run_execute(_EchoPlugin(), context, "ping") == "ping"


# --- Validation checks (18.13) -----------------------------------------------


def test_validator_approves_signed_compatible_plugin() -> None:
    report = _validator().validate(_EchoPlugin())
    assert report.approved
    assert all(c.status is not CheckStatus.FAILED for c in report.checks)


def test_validator_blocks_major_version_mismatch() -> None:
    report = _validator().validate(_EchoPlugin(compatible="2.0.0"))
    assert not report.approved
    assert any(
        c.name == "compatibility" and c.status is CheckStatus.FAILED
        for c in report.checks
    )


def test_validator_rejects_unsigned_when_required() -> None:
    report = _validator(_policy(require_signature=True)).validate(
        _EchoPlugin(signature=None)
    )
    assert not report.approved


def test_validator_permits_unsigned_when_allowed() -> None:
    report = _validator(
        _policy(require_signature=False, allow_unsigned=True)
    ).validate(_EchoPlugin(signature=None))
    assert report.approved


def test_validator_rejects_untrusted_publisher() -> None:
    policy = _policy(trusted_publishers=frozenset({"trusted-corp"}))
    report = _validator(policy).validate(_EchoPlugin(author="acme"))
    assert not report.approved


def test_validator_rejects_plugin_failing_sandbox_selfcheck() -> None:
    report = _validator().validate(_BrokenValidatePlugin())
    assert not report.approved
    assert any(
        c.name == "sandbox" and c.status is CheckStatus.FAILED for c in report.checks
    )


def test_validate_for_activation_raises_when_rejected() -> None:
    with pytest.raises(PluginError) as exc:
        _validator().validate_for_activation(_EchoPlugin(compatible="9.0.0"))
    assert exc.value.error_type is PluginErrorType.VALIDATION_FAILED


# --- Registry activation gating (18.10) --------------------------------------


def _registry(policy: PluginPolicy | None = None) -> PluginRegistry:
    sandbox = InProcessSandbox()
    return PluginRegistry(PluginValidator(policy or _policy(), sandbox), sandbox)


def test_registry_activates_valid_plugin() -> None:
    registry = _registry()
    result = registry.register(_EchoPlugin())
    assert result.status is PluginStatus.ACTIVE
    assert registry.is_active("echo")


def test_registry_rejects_invalid_plugin() -> None:
    registry = _registry()
    result = registry.register(_EchoPlugin(compatible="3.0.0"))
    assert result.status is PluginStatus.REJECTED
    assert not registry.is_active("echo")


def test_registry_executes_active_plugin() -> None:
    registry = _registry()
    registry.register(_EchoPlugin())
    context = PluginContext(tenant_id="t1")
    assert registry.execute("echo", context, "hello") == "hello"


def test_registry_refuses_execution_of_rejected_plugin() -> None:
    registry = _registry()
    registry.register(_EchoPlugin(compatible="3.0.0"))
    context = PluginContext(tenant_id="t1")
    with pytest.raises(PluginError) as exc:
        registry.execute("echo", context, "hello")
    assert exc.value.error_type is PluginErrorType.NOT_ACTIVATED


def test_registry_refuses_unknown_plugin() -> None:
    registry = _registry()
    context = PluginContext(tenant_id="t1")
    with pytest.raises(PluginError) as exc:
        registry.execute("ghost", context, "hello")
    assert exc.value.error_type is PluginErrorType.UNKNOWN_PLUGIN


def test_plugin_policy_from_settings_maps_values() -> None:
    policy = PluginPolicy.from_settings(
        PluginSettings(
            require_signature=False,
            allow_unsigned=True,
            trusted_publishers="a, b",
            ekie_version="2.1.0",
        )
    )
    assert policy.require_signature is False
    assert policy.trusted_publishers == frozenset({"a", "b"})
    assert policy.ekie_version == "2.1.0"

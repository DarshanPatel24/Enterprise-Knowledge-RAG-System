"""Manual demo for the EKIE Security, Governance and Extensibility engine (EKIE-S8).

Demonstrates the zero-trust and extensibility controls added in S8:
  * authentication to a typed principal (anonymous local-first + API key);
  * RBAC + ABAC authorization decisions;
  * per-stage policy enforcement with an append-only audit trail;
  * monotonic classification propagation (no downgrade);
  * secret resolution with log redaction;
  * plugin pre-activation sandbox validation and activation gating.

Runs fully offline using deterministic, dependency-free components.

Usage (from the repository root, with the project virtual environment):

    .\\.venv\\Scripts\\python.exe services/ekie/scripts/demo_security.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from domain.orchestration.state import StageName  # noqa: E402
from domain.plugins import (  # noqa: E402
    EKIEPlugin,
    InProcessSandbox,
    PluginContext,
    PluginManifest,
    PluginPolicy,
    PluginRegistry,
    PluginType,
    PluginValidator,
)
from domain.security import (  # noqa: E402
    AnonymousAuthenticator,
    ApiKeyAuthenticator,
    Classification,
    EnvSecretProvider,
    InMemoryAuditSink,
    PolicyEngine,
    Role,
    SecurityError,
    SecurityPolicy,
    StagePolicyGuard,
)


def _rule(title: str) -> None:
    print(f"\n=== {title} ===")


def _demo_authentication() -> None:
    _rule("Authentication (17.4)")
    policy = SecurityPolicy(
        anonymous_role=Role.SERVICE_WORKER,
        anonymous_clearance=Classification.RESTRICTED,
    )
    anon = AnonymousAuthenticator(policy).authenticate(None)
    print(f"anonymous principal: subject={anon.subject} roles={sorted(anon.roles)}")

    provider = EnvSecretProvider({"ingest_api_key": "s3cr3t-key"})
    authn = ApiKeyAuthenticator(
        provider,
        secret_name="ingest_api_key",  # noqa: S106 - secret name, not a secret value
        subject="ci-runner",
        roles=frozenset({Role.ENGINEER}),
        clearance=Classification.CONFIDENTIAL,
    )
    principal = authn.authenticate("s3cr3t-key")
    print(f"api-key principal:   subject={principal.subject} method={principal.method}")
    try:
        authn.authenticate("wrong-key")
    except SecurityError as exc:
        print(f"invalid key rejected: {exc.error_type}")


def _demo_stage_enforcement() -> None:
    _rule("Per-stage enforcement + audit (17.11, 17.14)")
    policy = SecurityPolicy()
    sink = InMemoryAuditSink()
    guard = StagePolicyGuard(policy, PolicyEngine(policy), sink)

    engineer = ApiKeyAuthenticator(
        EnvSecretProvider({"k": "v"}),
        secret_name="k",  # noqa: S106 - secret name, not a secret value
        subject="engineer-1",
        roles=frozenset({Role.ENGINEER}),
        clearance=Classification.RESTRICTED,
    ).authenticate("v")

    for stage in StageName:
        guard.authorize_stage(
            engineer, stage, Classification.CONFIDENTIAL, resource="doc-42"
        )
    print(f"engineer authorized for all {len(list(StageName))} stages")

    viewer = AnonymousAuthenticator(
        SecurityPolicy(
            anonymous_role=Role.VIEWER, anonymous_clearance=Classification.PUBLIC
        )
    ).authenticate(None)
    try:
        guard.authorize_stage(
            viewer, StageName.PUBLISH, Classification.PUBLIC, resource="doc-42"
        )
    except SecurityError as exc:
        print(f"viewer denied publish: {exc.error_type}")
    print(f"audit trail entries: {len(sink.history())}")


def _demo_classification() -> None:
    _rule("Classification propagation (17.7)")
    policy = SecurityPolicy()
    guard = StagePolicyGuard(policy, PolicyEngine(policy), InMemoryAuditSink())
    result = guard.propagate_classification(
        Classification.INTERNAL,
        Classification.CONFIDENTIAL,
        actor="svc",
        resource="doc-42",
    )
    print(f"internal -> confidential permitted: {result}")
    try:
        guard.propagate_classification(
            Classification.CONFIDENTIAL,
            Classification.PUBLIC,
            actor="svc",
            resource="doc-42",
        )
    except SecurityError as exc:
        print(f"confidential -> public blocked: {exc.error_type}")


def _demo_secret_redaction() -> None:
    _rule("Secret resolution + redaction (17.8)")
    provider = EnvSecretProvider({"db_password": "hunter2"})
    provider.resolve("db_password")
    print(f"tracked secret values for redaction: {len(provider.registry.values())}")
    print("(the RedactionFilter scrubs these from every structured log record)")


class _UpperCasePlugin(EKIEPlugin):
    """A trivial parser plugin that upper-cases its input."""

    def __init__(self, *, version: str = "1.0.0", signature: str | None = "sig") -> None:
        self._manifest = PluginManifest(
            name="uppercase",
            version="1.0.0",
            plugin_type=PluginType.PARSER,
            compatible_ekie_versions=version,
            author="acme",
            description="upper-cases text",
            signature=signature,
        )

    def metadata(self) -> PluginManifest:
        return self._manifest

    def validate(self) -> None:
        return None

    def initialize(self, context: PluginContext) -> None:
        return None

    def execute(self, input_data: Any) -> Any:  # noqa: ANN401
        return str(input_data).upper()


def _demo_plugins() -> None:
    _rule("Plugin sandbox validation + activation (18.13)")
    sandbox = InProcessSandbox()
    validator = PluginValidator(PluginPolicy(), sandbox)
    registry = PluginRegistry(validator, sandbox)

    ok = registry.register(_UpperCasePlugin())
    print(f"valid plugin -> {ok.status}")
    context = PluginContext(tenant_id="t1")
    print(f"execute active plugin: {registry.execute('uppercase', context, 'hello')}")

    bad = registry.register(_UpperCasePlugin(version="9.0.0"))
    print(f"incompatible plugin -> {bad.status} (failures: {len(bad.report.failures)})")
    unsigned = registry.register(
        _UpperCasePlugin(signature=None),
    )
    print(f"unsigned plugin (signature required) -> {unsigned.status}")


def main() -> None:
    """Run the security and extensibility demonstration."""
    _demo_authentication()
    _demo_stage_enforcement()
    _demo_classification()
    _demo_secret_redaction()
    _demo_plugins()
    print("\nDemo complete.")


if __name__ == "__main__":
    main()

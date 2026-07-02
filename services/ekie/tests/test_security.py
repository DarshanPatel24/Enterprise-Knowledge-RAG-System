"""Tests for the security, governance, and classification module (EKIE-S8)."""

from __future__ import annotations

import logging

import pytest

from domain.orchestration.state import StageName
from domain.security import (
    AccessRequest,
    AnonymousAuthenticator,
    ApiKeyAuthenticator,
    AuditAction,
    AuditResult,
    Classification,
    EnvSecretProvider,
    InMemoryAuditSink,
    Permission,
    PolicyEngine,
    Principal,
    RedactionFilter,
    Role,
    SecretRegistry,
    SecurityError,
    SecurityErrorType,
    SecurityPolicy,
    StagePolicyGuard,
    ensure_no_downgrade,
    is_cleared,
    parse_classification,
    rank,
)
from domain.security.audit import AuditRecord
from domain.security.identity import AuthMethod


def _policy(**overrides: object) -> SecurityPolicy:
    return SecurityPolicy(**overrides)  # type: ignore[arg-type]


def _principal(
    *,
    roles: frozenset[Role],
    clearance: Classification = Classification.RESTRICTED,
) -> Principal:
    return Principal(
        subject="svc",
        method=AuthMethod.SERVICE_IDENTITY,
        roles=roles,
        clearance=clearance,
    )


# --- Classification propagation (S8-4) ---------------------------------------


def test_classification_rank_is_ordered() -> None:
    assert rank(Classification.PUBLIC) < rank(Classification.INTERNAL)
    assert rank(Classification.HIGHLY_CONFIDENTIAL) < rank(Classification.RESTRICTED)


def test_parse_classification_is_case_insensitive() -> None:
    assert parse_classification("  Confidential ") is Classification.CONFIDENTIAL


def test_parse_classification_rejects_unknown() -> None:
    with pytest.raises(SecurityError) as exc:
        parse_classification("top_secret")
    assert exc.value.error_type is SecurityErrorType.UNKNOWN_CLASSIFICATION


def test_ensure_no_downgrade_allows_same_or_higher() -> None:
    assert (
        ensure_no_downgrade(Classification.INTERNAL, Classification.CONFIDENTIAL)
        is Classification.CONFIDENTIAL
    )
    assert (
        ensure_no_downgrade(Classification.INTERNAL, Classification.INTERNAL)
        is Classification.INTERNAL
    )


def test_ensure_no_downgrade_blocks_downgrade() -> None:
    with pytest.raises(SecurityError) as exc:
        ensure_no_downgrade(Classification.CONFIDENTIAL, Classification.PUBLIC)
    assert exc.value.error_type is SecurityErrorType.CLEARANCE_VIOLATION


def test_ensure_no_downgrade_permits_downgrade_when_allowed() -> None:
    assert (
        ensure_no_downgrade(
            Classification.CONFIDENTIAL,
            Classification.PUBLIC,
            allow_downgrade=True,
        )
        is Classification.PUBLIC
    )


def test_is_cleared_respects_ordering() -> None:
    assert is_cleared(Classification.RESTRICTED, Classification.CONFIDENTIAL)
    assert not is_cleared(Classification.PUBLIC, Classification.CONFIDENTIAL)


# --- Authentication (S8-1) ---------------------------------------------------


def test_anonymous_authenticator_uses_policy_defaults() -> None:
    policy = _policy(
        anonymous_role=Role.VIEWER, anonymous_clearance=Classification.INTERNAL
    )
    principal = AnonymousAuthenticator(policy).authenticate(None)
    assert principal.method is AuthMethod.ANONYMOUS
    assert principal.roles == frozenset({Role.VIEWER})
    assert principal.clearance is Classification.INTERNAL


def test_api_key_authenticator_accepts_valid_key() -> None:
    provider = EnvSecretProvider({"ingest_api_key": "s3cr3t"})
    authn = ApiKeyAuthenticator(
        provider,
        secret_name="ingest_api_key",
        subject="ci-runner",
        roles=frozenset({Role.ENGINEER}),
        clearance=Classification.CONFIDENTIAL,
    )
    principal = authn.authenticate("s3cr3t")
    assert principal.subject == "ci-runner"
    assert principal.method is AuthMethod.API_KEY


def test_api_key_authenticator_rejects_invalid_key() -> None:
    provider = EnvSecretProvider({"ingest_api_key": "s3cr3t"})
    authn = ApiKeyAuthenticator(
        provider,
        secret_name="ingest_api_key",
        subject="ci-runner",
        roles=frozenset({Role.ENGINEER}),
        clearance=Classification.CONFIDENTIAL,
    )
    with pytest.raises(SecurityError) as exc:
        authn.authenticate("wrong")
    assert exc.value.error_type is SecurityErrorType.UNAUTHENTICATED


def test_api_key_authenticator_requires_credential() -> None:
    provider = EnvSecretProvider({"ingest_api_key": "s3cr3t"})
    authn = ApiKeyAuthenticator(
        provider,
        secret_name="ingest_api_key",
        subject="ci-runner",
        roles=frozenset({Role.ENGINEER}),
        clearance=Classification.CONFIDENTIAL,
    )
    with pytest.raises(SecurityError):
        authn.authenticate(None)


# --- Authorization: RBAC + ABAC (S8-1, S8-2) ---------------------------------


def test_policy_engine_grants_role_permission_with_clearance() -> None:
    engine = PolicyEngine(_policy())
    request = AccessRequest(
        principal=_principal(roles=frozenset({Role.ENGINEER})),
        permission=Permission.PUBLISH,
        resource_classification=Classification.CONFIDENTIAL,
    )
    decision = engine.evaluate(request)
    assert decision.allowed


def test_policy_engine_denies_missing_permission() -> None:
    engine = PolicyEngine(_policy())
    request = AccessRequest(
        principal=_principal(roles=frozenset({Role.VIEWER})),
        permission=Permission.PUBLISH,
        resource_classification=Classification.PUBLIC,
    )
    decision = engine.evaluate(request)
    assert not decision.allowed
    assert "role_missing_permission" in decision.reason


def test_policy_engine_denies_insufficient_clearance() -> None:
    engine = PolicyEngine(_policy())
    request = AccessRequest(
        principal=_principal(
            roles=frozenset({Role.ENGINEER}), clearance=Classification.PUBLIC
        ),
        permission=Permission.EMBED,
        resource_classification=Classification.RESTRICTED,
    )
    decision = engine.evaluate(request)
    assert not decision.allowed
    assert "insufficient_clearance" in decision.reason


def test_policy_engine_authorize_raises_on_deny() -> None:
    engine = PolicyEngine(_policy())
    request = AccessRequest(
        principal=_principal(roles=frozenset({Role.VIEWER})),
        permission=Permission.EMBED,
        resource_classification=Classification.PUBLIC,
    )
    with pytest.raises(SecurityError) as exc:
        engine.authorize(request)
    assert exc.value.error_type is SecurityErrorType.UNAUTHORIZED


def test_authorization_disabled_allows_everything() -> None:
    engine = PolicyEngine(_policy(enforce_authorization=False))
    request = AccessRequest(
        principal=_principal(roles=frozenset({Role.VIEWER})),
        permission=Permission.PUBLISH,
        resource_classification=Classification.RESTRICTED,
    )
    assert engine.evaluate(request).allowed


# --- Secrets and log redaction (S8-1) ----------------------------------------


def test_secret_provider_registers_value_for_redaction() -> None:
    registry = SecretRegistry()
    provider = EnvSecretProvider({"db_password": "hunter2"}, registry=registry)
    assert provider.resolve("db_password") == "hunter2"
    assert "hunter2" in registry.values()


def test_secret_provider_raises_when_absent() -> None:
    provider = EnvSecretProvider({})
    with pytest.raises(SecurityError) as exc:
        provider.resolve("missing")
    assert exc.value.error_type is SecurityErrorType.SECRET_UNAVAILABLE


def test_redaction_filter_masks_registered_secret() -> None:
    registry = SecretRegistry()
    registry.register("hunter2")
    log_filter = RedactionFilter(registry)
    record = logging.LogRecord(
        name="ekie.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="connecting with hunter2",
        args=(),
        exc_info=None,
    )
    assert log_filter.filter(record) is True
    assert "hunter2" not in record.getMessage()


def test_redaction_filter_masks_sensitive_field_names() -> None:
    log_filter = RedactionFilter(SecretRegistry())
    record = logging.LogRecord(
        name="ekie.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="event",
        args=(),
        exc_info=None,
    )
    record.password = "plaintext"  # type: ignore[attr-defined]  # noqa: S105
    log_filter.filter(record)
    assert record.password == "***redacted***"  # type: ignore[attr-defined]  # noqa: S105


# --- Audit trail (S8-2) ------------------------------------------------------


def test_in_memory_audit_sink_is_append_only() -> None:
    sink = InMemoryAuditSink()
    sink.record(
        AuditRecord(
            actor="svc",
            action=AuditAction.DOCUMENT_INGESTED,
            resource="doc-1",
            result=AuditResult.ALLOW,
        )
    )
    history = sink.history()
    assert len(history) == 1
    assert history[0].action is AuditAction.DOCUMENT_INGESTED


# --- Per-stage enforcement (S8-2, S8-4) --------------------------------------


def _guard(policy: SecurityPolicy, sink: InMemoryAuditSink) -> StagePolicyGuard:
    return StagePolicyGuard(policy, PolicyEngine(policy), sink)


def test_stage_guard_authorizes_and_audits() -> None:
    sink = InMemoryAuditSink()
    guard = _guard(_policy(), sink)
    guard.authorize_stage(
        _principal(roles=frozenset({Role.ENGINEER})),
        StageName.EMBED,
        Classification.CONFIDENTIAL,
        resource="doc-1",
    )
    history = sink.history()
    assert history[-1].action is AuditAction.STAGE_AUTHORIZED
    assert history[-1].result is AuditResult.ALLOW


def test_stage_guard_denies_and_audits() -> None:
    sink = InMemoryAuditSink()
    guard = _guard(_policy(), sink)
    with pytest.raises(SecurityError) as exc:
        guard.authorize_stage(
            _principal(roles=frozenset({Role.VIEWER})),
            StageName.PUBLISH,
            Classification.PUBLIC,
            resource="doc-1",
        )
    assert exc.value.error_type is SecurityErrorType.UNAUTHORIZED
    assert sink.history()[-1].action is AuditAction.STAGE_DENIED


def test_stage_guard_propagates_classification() -> None:
    sink = InMemoryAuditSink()
    guard = _guard(_policy(), sink)
    result = guard.propagate_classification(
        Classification.INTERNAL,
        Classification.CONFIDENTIAL,
        actor="svc",
        resource="doc-1",
    )
    assert result is Classification.CONFIDENTIAL
    assert sink.history()[-1].action is AuditAction.CLASSIFICATION_PROPAGATED


def test_stage_guard_blocks_downgrade_and_audits_violation() -> None:
    sink = InMemoryAuditSink()
    guard = _guard(_policy(), sink)
    with pytest.raises(SecurityError):
        guard.propagate_classification(
            Classification.CONFIDENTIAL,
            Classification.PUBLIC,
            actor="svc",
            resource="doc-1",
        )
    assert sink.history()[-1].action is AuditAction.CLASSIFICATION_VIOLATION


def test_stage_guard_skips_audit_when_disabled() -> None:
    sink = InMemoryAuditSink()
    guard = _guard(_policy(enable_audit=False), sink)
    guard.authorize_stage(
        _principal(roles=frozenset({Role.ENGINEER})),
        StageName.TRANSFORM,
        Classification.INTERNAL,
        resource="doc-1",
    )
    assert sink.history() == ()


def test_security_policy_from_settings_maps_values() -> None:
    from config.settings import GovernanceSettings, SecuritySettings

    policy = SecurityPolicy.from_settings(
        SecuritySettings(anonymous_role="viewer", anonymous_clearance="internal"),
        GovernanceSettings(allow_classification_downgrade=True),
    )
    assert policy.anonymous_role is Role.VIEWER
    assert policy.anonymous_clearance is Classification.INTERNAL
    assert policy.allow_classification_downgrade is True

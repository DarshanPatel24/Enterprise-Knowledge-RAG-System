"""Tests for the governance domain: policy, audit, masking, propagation."""

from __future__ import annotations

import pytest

from config.settings import GovernanceSettings
from contracts.enums import ClassificationClearance
from domain.governance import (
    AccessRequest,
    AuditAction,
    AuditResult,
    GovernanceError,
    GovernancePolicy,
    InMemoryAuditSink,
    Masker,
    MaskingConfig,
    Permission,
    PolicyEngine,
    Principal,
    Role,
    SecurityContextPropagator,
    ensure_no_downgrade,
    is_cleared,
    parse_clearance,
)
from domain.governance.guard import GovernanceGuard


def _principal(
    *, roles: frozenset[Role], clearance: ClassificationClearance
) -> Principal:
    return Principal(
        user_id="analyst-1", tenant_id="tenant-a", roles=roles, clearance=clearance
    )


def test_policy_grants_when_role_has_permission() -> None:
    engine = PolicyEngine()
    decision = engine.evaluate(
        AccessRequest(
            principal=_principal(
                roles=frozenset({Role.POWER_USER}),
                clearance=ClassificationClearance.INTERNAL,
            ),
            permission=Permission.INVOKE_AGENT,
            resource="agent",
        )
    )
    assert decision.allowed is True
    assert decision.reason == "granted"


def test_policy_denies_when_role_missing_permission() -> None:
    engine = PolicyEngine()
    decision = engine.evaluate(
        AccessRequest(
            principal=_principal(
                roles=frozenset({Role.USER}),
                clearance=ClassificationClearance.INTERNAL,
            ),
            permission=Permission.INVOKE_AGENT,
            resource="agent",
        )
    )
    assert decision.allowed is False
    assert "role_missing_permission" in decision.reason


def test_policy_denies_on_insufficient_clearance() -> None:
    engine = PolicyEngine()
    with pytest.raises(GovernanceError):
        engine.authorize(
            AccessRequest(
                principal=_principal(
                    roles=frozenset({Role.ADMIN}),
                    clearance=ClassificationClearance.PUBLIC,
                ),
                permission=Permission.READ_MEMORY,
                resource="memory",
                resource_classification=ClassificationClearance.RESTRICTED,
            )
        )


def test_enforcement_disabled_allows_everything() -> None:
    engine = PolicyEngine(enforce_authorization=False)
    decision = engine.evaluate(
        AccessRequest(
            principal=_principal(
                roles=frozenset(), clearance=ClassificationClearance.PUBLIC
            ),
            permission=Permission.MANAGE_POLICY,
            resource="policy",
        )
    )
    assert decision.allowed is True


def test_clearance_helpers() -> None:
    assert is_cleared(
        ClassificationClearance.RESTRICTED, ClassificationClearance.INTERNAL
    )
    assert not is_cleared(
        ClassificationClearance.PUBLIC, ClassificationClearance.CONFIDENTIAL
    )
    assert parse_clearance("internal") is ClassificationClearance.INTERNAL
    with pytest.raises(GovernanceError):
        parse_clearance("cosmic-top-secret")


def test_no_downgrade_enforced() -> None:
    with pytest.raises(GovernanceError):
        ensure_no_downgrade(
            ClassificationClearance.CONFIDENTIAL, ClassificationClearance.PUBLIC
        )
    assert (
        ensure_no_downgrade(
            ClassificationClearance.PUBLIC, ClassificationClearance.CONFIDENTIAL
        )
        is ClassificationClearance.CONFIDENTIAL
    )


def test_masker_redacts_pii() -> None:
    masker = Masker(MaskingConfig())
    masked, count = masker.mask_text(
        "Contact me at jane@acme.com or 555-123-4567; SSN 123-45-6789"
    )
    assert "jane@acme.com" not in masked
    assert "[REDACTED-EMAIL]" in masked
    assert "[REDACTED-SSN]" in masked
    assert count >= 3


def test_masker_disabled_is_noop() -> None:
    masker = Masker(MaskingConfig(enabled=False))
    masked, count = masker.mask_text("jane@acme.com")
    assert masked == "jane@acme.com"
    assert count == 0


def _guard(**overrides: object) -> GovernanceGuard:
    settings = GovernanceSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    policy = GovernancePolicy.from_settings(settings)
    return GovernanceGuard(
        PolicyEngine(policy_version=policy.policy_version),
        InMemoryAuditSink(),
        Masker(MaskingConfig()),
        SecurityContextPropagator(),
        policy=policy,
    )


def test_guard_audits_grant_and_denial() -> None:
    guard = _guard()
    sink = guard.audit_sink
    assert isinstance(sink, InMemoryAuditSink)

    guard.authorize(
        _principal(
            roles=frozenset({Role.POWER_USER}),
            clearance=ClassificationClearance.INTERNAL,
        ),
        Permission.INVOKE_AGENT,
        "agent",
    )
    with pytest.raises(GovernanceError):
        guard.authorize(
            _principal(
                roles=frozenset({Role.USER}),
                clearance=ClassificationClearance.INTERNAL,
            ),
            Permission.INVOKE_AGENT,
            "agent",
        )
    actions = [record.action for record in sink.history()]
    assert AuditAction.AGENT_INVOKED in actions
    assert AuditAction.AGENT_DENIED in actions
    results = [record.result for record in sink.history()]
    assert AuditResult.DENIED in results


def test_guard_propagates_security_context() -> None:
    guard = _guard()
    payload = guard.propagate_security_context(
        _principal(
            roles=frozenset({Role.USER}), clearance=ClassificationClearance.CONFIDENTIAL
        )
    )
    assert payload == {
        "user_id": "analyst-1",
        "tenant_id": "tenant-a",
        "classification_clearance": "confidential",
    }


def test_guard_masks_and_audits_response() -> None:
    guard = _guard()
    sink = guard.audit_sink
    assert isinstance(sink, InMemoryAuditSink)
    masked, count = guard.mask_response(
        "Reach me at bob@acme.com", actor="analyst-1", tenant_id="tenant-a"
    )
    assert "[REDACTED-EMAIL]" in masked
    assert count == 1
    assert any(
        record.action is AuditAction.RESPONSE_FILTERED for record in sink.history()
    )

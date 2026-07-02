"""Tests for the EKIE-S8 security and plugin composition builders."""

from __future__ import annotations

from composition import (
    build_plugin_registry,
    build_secret_provider,
    build_security_policy,
    build_stage_guard,
)
from config.settings import EkieSettings
from domain.security import Classification, InMemoryAuditSink, Role


def test_build_security_policy_reads_settings() -> None:
    settings = EkieSettings()
    policy = build_security_policy(settings)
    assert policy.enforce_authorization is True
    assert policy.anonymous_role is Role.SERVICE_WORKER
    assert policy.anonymous_clearance is Classification.RESTRICTED


def test_build_secret_provider_primes_redaction() -> None:
    settings = EkieSettings()
    settings = settings.model_copy(
        update={
            "storage": settings.storage.model_copy(
                update={"secret_key": "minio-secret"}
            )
        }
    )
    provider = build_secret_provider(settings)
    assert "minio-secret" in provider.registry.values()


def test_build_stage_guard_uses_injected_sink() -> None:
    settings = EkieSettings()
    sink = InMemoryAuditSink()
    guard = build_stage_guard(settings, audit_sink=sink)
    assert guard is not None


def test_build_plugin_registry_is_constructed() -> None:
    registry = build_plugin_registry(EkieSettings())
    assert registry.status_of("anything") is None

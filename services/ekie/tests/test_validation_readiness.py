"""Deployment, HA, and DR readiness tests (EKIE-S9-4)."""

from __future__ import annotations

from config.settings import DeploymentSettings, EkieSettings, StorageSettings
from domain.validation import Severity, assess_readiness


def test_local_defaults_are_ready() -> None:
    report = assess_readiness(EkieSettings())
    assert report.passed
    assert any(
        f.check == "readiness.deployment" and f.severity is Severity.INFO
        for f in report.findings
    )


def test_invalid_dr_targets_fail() -> None:
    settings = EkieSettings(
        deployment=DeploymentSettings(rpo_seconds=600.0, rto_seconds=300.0)
    )
    report = assess_readiness(settings)
    assert not report.passed
    assert any(f.check == "readiness.dr" for f in report.errors)


def test_non_local_requires_storage_credentials() -> None:
    settings = EkieSettings(
        environment="production",
        storage=StorageSettings(access_key="", secret_key=""),
        deployment=DeploymentSettings(replicas=3),
    )
    report = assess_readiness(settings)
    assert not report.passed
    assert any(f.check == "readiness.storage" for f in report.errors)


def test_non_local_single_replica_warns() -> None:
    settings = EkieSettings(
        environment="production",
        storage=StorageSettings(access_key="k", secret_key="s"),
        deployment=DeploymentSettings(replicas=1),
    )
    report = assess_readiness(settings)
    assert any(
        f.check == "readiness.ha" and f.severity is Severity.WARNING
        for f in report.findings
    )

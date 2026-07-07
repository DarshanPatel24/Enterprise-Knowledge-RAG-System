"""Tests for the EKCP security context ingress validator."""

from __future__ import annotations

import pytest

from config.settings import SecuritySettings
from domain.security import (
    SecurityContextValidator,
    SecurityError,
    SecurityErrorType,
)


def _validator(*, require: bool) -> SecurityContextValidator:
    return SecurityContextValidator.from_settings(
        SecuritySettings(_env_file=None, require_security_context=require)
    )


def test_valid_context() -> None:
    context = _validator(require=True).validate(
        {
            "user_id": "analyst-1",
            "tenant_id": "tenant-a",
            "classification_clearance": "internal",
        },
        expected_tenant_id="tenant-a",
    )
    assert context is not None
    assert context.user_id == "analyst-1"
    assert context.tenant_id == "tenant-a"


def test_missing_context_when_required_raises() -> None:
    with pytest.raises(SecurityError) as exc:
        _validator(require=True).validate(None)
    assert exc.value.error_type == SecurityErrorType.MISSING_CONTEXT


def test_missing_context_when_optional_returns_none() -> None:
    assert _validator(require=False).validate(None) is None


def test_tenant_mismatch_raises() -> None:
    with pytest.raises(SecurityError) as exc:
        _validator(require=True).validate(
            {
                "user_id": "analyst-1",
                "tenant_id": "tenant-b",
                "classification_clearance": "internal",
            },
            expected_tenant_id="tenant-a",
        )
    assert exc.value.error_type == SecurityErrorType.TENANT_MISMATCH


def test_unknown_clearance_raises() -> None:
    with pytest.raises(SecurityError) as exc:
        _validator(require=True).validate(
            {
                "user_id": "analyst-1",
                "tenant_id": "tenant-a",
                "classification_clearance": "top-secret",
            }
        )
    assert exc.value.error_type == SecurityErrorType.UNKNOWN_CLEARANCE

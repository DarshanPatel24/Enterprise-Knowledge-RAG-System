"""Tests for security context ingress validation."""

from __future__ import annotations

import pytest

from contracts.enums import ClassificationClearance
from domain.security import (
    SecurityContextValidator,
    SecurityError,
    SecurityErrorType,
)


def _validator(*, require: bool = True) -> SecurityContextValidator:
    return SecurityContextValidator(require_security_context=require)


def test_valid_context_is_normalized() -> None:
    context = _validator().validate(
        {
            "user_id": "u-1",
            "tenant_id": "tenant-a",
            "classification_clearance": "internal",
        }
    )
    assert context is not None
    assert context.user_id == "u-1"
    assert context.tenant_id == "tenant-a"
    assert context.classification_clearance is ClassificationClearance.INTERNAL


def test_missing_context_required_raises() -> None:
    with pytest.raises(SecurityError) as exc:
        _validator().validate(None)
    assert exc.value.error_type is SecurityErrorType.MISSING_CONTEXT


def test_missing_context_optional_returns_none() -> None:
    assert _validator(require=False).validate(None) is None


def test_missing_tenant_raises() -> None:
    with pytest.raises(SecurityError) as exc:
        _validator().validate({"user_id": "u-1", "classification_clearance": "public"})
    assert exc.value.error_type is SecurityErrorType.INVALID_TENANT


def test_unknown_clearance_raises() -> None:
    with pytest.raises(SecurityError) as exc:
        _validator().validate(
            {
                "user_id": "u-1",
                "tenant_id": "tenant-a",
                "classification_clearance": "top-secret",
            }
        )
    assert exc.value.error_type is SecurityErrorType.UNKNOWN_CLEARANCE


def test_tenant_mismatch_raises() -> None:
    with pytest.raises(SecurityError) as exc:
        _validator().validate(
            {
                "user_id": "u-1",
                "tenant_id": "tenant-a",
                "classification_clearance": "public",
            },
            expected_tenant_id="tenant-b",
        )
    assert exc.value.error_type is SecurityErrorType.TENANT_MISMATCH

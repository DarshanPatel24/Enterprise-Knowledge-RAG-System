"""Tests for signed security-context verification (the caller trust boundary)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

import pytest

from contracts.enums import ClassificationClearance
from domain.security import (
    SecurityContextValidator,
    SecurityError,
    SecurityErrorType,
    SignedContextVerifier,
)

_SECRET = "test-signing-secret"  # noqa: S105 - test-only HMAC secret
_DIGEST = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _mint(payload: dict[str, object], *, secret: str = _SECRET, alg: str = "HS256") -> str:
    header = _b64(json.dumps({"alg": alg, "typ": "JWT"}).encode())
    body = _b64(json.dumps(payload).encode())
    signing_input = f"{header}.{body}".encode()
    signature = hmac.new(secret.encode(), signing_input, _DIGEST[alg]).digest()
    return f"{header}.{body}.{_b64(signature)}"


def _claims(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "user_id": "u-1",
        "tenant_id": "tenant-a",
        "classification_clearance": "confidential",
        "exp": time.time() + 300,
    }
    base.update(overrides)
    return base


def test_valid_token_yields_context() -> None:
    verifier = SignedContextVerifier(secret=_SECRET)
    context = verifier.verify(_mint(_claims()))
    assert context.user_id == "u-1"
    assert context.tenant_id == "tenant-a"
    assert context.classification_clearance is ClassificationClearance.CONFIDENTIAL


def test_tampered_signature_is_rejected() -> None:
    verifier = SignedContextVerifier(secret=_SECRET)
    token = _mint(_claims())
    forged = token[:-4] + ("aaaa" if not token.endswith("aaaa") else "bbbb")
    with pytest.raises(SecurityError) as exc:
        verifier.verify(forged)
    assert exc.value.error_type is SecurityErrorType.INVALID_SIGNATURE


def test_wrong_secret_is_rejected() -> None:
    verifier = SignedContextVerifier(secret=_SECRET)
    with pytest.raises(SecurityError) as exc:
        verifier.verify(_mint(_claims(), secret="other-secret"))
    assert exc.value.error_type is SecurityErrorType.INVALID_SIGNATURE


def test_expired_token_is_rejected() -> None:
    verifier = SignedContextVerifier(secret=_SECRET, leeway_seconds=0)
    with pytest.raises(SecurityError) as exc:
        verifier.verify(_mint(_claims(exp=time.time() - 10)))
    assert exc.value.error_type is SecurityErrorType.INVALID_SIGNATURE


def test_algorithm_none_is_rejected() -> None:
    verifier = SignedContextVerifier(secret=_SECRET)
    header = _b64(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    body = _b64(json.dumps(_claims()).encode())
    token = f"{header}.{body}."
    with pytest.raises(SecurityError) as exc:
        verifier.verify(token)
    assert exc.value.error_type is SecurityErrorType.INVALID_SIGNATURE


def test_wrong_audience_is_rejected() -> None:
    verifier = SignedContextVerifier(secret=_SECRET, audience="ekre")
    with pytest.raises(SecurityError) as exc:
        verifier.verify(_mint(_claims(aud="other")))
    assert exc.value.error_type is SecurityErrorType.INVALID_SIGNATURE


def test_matching_audience_and_issuer_pass() -> None:
    verifier = SignedContextVerifier(secret=_SECRET, audience="ekre", issuer="ekcp")
    context = verifier.verify(_mint(_claims(aud="ekre", iss="ekcp")))
    assert context.tenant_id == "tenant-a"


def test_missing_secret_is_misconfigured() -> None:
    verifier = SignedContextVerifier(secret="")
    with pytest.raises(SecurityError) as exc:
        verifier.verify(_mint(_claims()))
    assert exc.value.error_type is SecurityErrorType.INVALID_SIGNATURE


def test_validator_signed_path_requires_token() -> None:
    validator = SecurityContextValidator(
        require_security_context=True,
        verifier=SignedContextVerifier(secret=_SECRET),
    )
    with pytest.raises(SecurityError) as exc:
        validator.validate(None, expected_tenant_id="tenant-a", signed_token=None)
    assert exc.value.error_type is SecurityErrorType.MISSING_CONTEXT


def test_validator_signed_path_returns_verified_context() -> None:
    validator = SecurityContextValidator(
        require_security_context=True,
        verifier=SignedContextVerifier(secret=_SECRET),
    )
    context = validator.validate(
        None, expected_tenant_id="tenant-a", signed_token=_mint(_claims())
    )
    assert context is not None
    assert context.tenant_id == "tenant-a"


def test_validator_signed_path_rejects_tenant_mismatch() -> None:
    validator = SecurityContextValidator(
        require_security_context=True,
        verifier=SignedContextVerifier(secret=_SECRET),
    )
    with pytest.raises(SecurityError) as exc:
        validator.validate(
            None, expected_tenant_id="tenant-b", signed_token=_mint(_claims())
        )
    assert exc.value.error_type is SecurityErrorType.TENANT_MISMATCH

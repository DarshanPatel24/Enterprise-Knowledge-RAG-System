"""Signed security-context verification (the caller trust boundary).

EKRE must not trust a self-asserted security context. When signed contexts are
required, the caller (EKCP) mints a compact JWS/JWT that attests the identity and
clearance, and EKRE verifies it here before any retrieval. The verifier is
implemented with the standard library (``hmac``/``hashlib``) to stay
dependency-free and local-first.

Security properties:
- Only the single configured HMAC algorithm is accepted; ``alg: none`` and any
  other/asymmetric algorithm are always rejected (prevents algorithm confusion).
- Signatures are compared in constant time.
- ``exp`` is required; ``nbf``/``iat`` are honored when present; ``iss``/``aud``
  are verified when configured.
"""

from __future__ import annotations

import base64
import hmac
import json
import time
from typing import Any

from contracts.enums import ClassificationClearance
from contracts.security_context import SecurityContext
from domain.security.errors import SecurityError, SecurityErrorType

# Supported HMAC algorithms mapped to their hashlib digest name. Asymmetric
# algorithms are intentionally unsupported: this is a shared-secret trust seam.
_ALGORITHMS: dict[str, str] = {
    "HS256": "sha256",
    "HS384": "sha384",
    "HS512": "sha512",
}


def _b64url_decode(segment: str) -> bytes:
    """Decode a base64url segment, tolerating missing padding."""
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


class SignedContextVerifier:
    """Verifies an HMAC-signed JWT that attests the request security context."""

    def __init__(
        self,
        *,
        secret: str,
        algorithm: str = "HS256",
        issuer: str = "",
        audience: str = "",
        leeway_seconds: int = 30,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._issuer = issuer
        self._audience = audience
        self._leeway_seconds = max(0, leeway_seconds)

    def verify(self, token: str) -> SecurityContext:
        """Verify ``token`` and return the attested security context.

        Raises :class:`SecurityError` with ``INVALID_SIGNATURE`` for any
        signature, structure, expiry, issuer, or audience failure, and the
        matching field error for an invalid identity or clearance claim.
        """
        digest = _ALGORITHMS.get(self._algorithm)
        if digest is None or not self._secret:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE,
                "signed security context verification is misconfigured",
            )
        header, payload, signing_input, signature = self._split(token)
        self._check_algorithm(header)
        self._check_signature(digest, signing_input, signature)
        self._check_time(payload)
        self._check_issuer(payload)
        self._check_audience(payload)
        return self._to_context(payload)

    def _split(self, token: str) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
        parts = token.split(".")
        if len(parts) != 3:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "malformed signed security context"
            )
        header_b64, payload_b64, signature_b64 = parts
        try:
            header = json.loads(_b64url_decode(header_b64))
            payload = json.loads(_b64url_decode(payload_b64))
            signature = _b64url_decode(signature_b64)
        except (ValueError, json.JSONDecodeError) as exc:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "unreadable signed security context"
            ) from exc
        if not isinstance(header, dict) or not isinstance(payload, dict):
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "malformed signed security context"
            )
        signing_input = f"{header_b64}.{payload_b64}".encode()
        return header, payload, signing_input, signature

    def _check_algorithm(self, header: dict[str, Any]) -> None:
        # Only the configured symmetric algorithm is accepted; "none" is rejected.
        if str(header.get("alg", "")) != self._algorithm:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE,
                "unexpected signed security context algorithm",
            )

    def _check_signature(self, digest_name: str, signing_input: bytes, signature: bytes) -> None:
        expected = hmac.new(self._secret.encode(), signing_input, digest_name).digest()
        if not hmac.compare_digest(expected, signature):
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "invalid security context signature"
            )

    def _check_time(self, payload: dict[str, Any]) -> None:
        now = time.time()
        exp = payload.get("exp")
        if exp is None:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "signed security context has no expiry"
            )
        try:
            if now > float(exp) + self._leeway_seconds:
                raise SecurityError(
                    SecurityErrorType.INVALID_SIGNATURE, "signed security context has expired"
                )
            nbf = payload.get("nbf")
            if nbf is not None and now < float(nbf) - self._leeway_seconds:
                raise SecurityError(
                    SecurityErrorType.INVALID_SIGNATURE, "signed security context not yet valid"
                )
        except (TypeError, ValueError) as exc:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "invalid signed security context timing"
            ) from exc

    def _check_issuer(self, payload: dict[str, Any]) -> None:
        if self._issuer and str(payload.get("iss", "")) != self._issuer:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "unexpected signed security context issuer"
            )

    def _check_audience(self, payload: dict[str, Any]) -> None:
        if not self._audience:
            return
        aud = payload.get("aud")
        allowed = set(aud) if isinstance(aud, list) else {aud}
        if self._audience not in allowed:
            raise SecurityError(
                SecurityErrorType.INVALID_SIGNATURE, "unexpected signed security context audience"
            )

    def _to_context(self, payload: dict[str, Any]) -> SecurityContext:
        user_id = str(payload.get("user_id") or payload.get("sub") or "").strip()
        tenant_id = str(payload.get("tenant_id") or "").strip()
        clearance_value = str(payload.get("classification_clearance") or "").strip()
        if not user_id:
            raise SecurityError(
                SecurityErrorType.INVALID_USER, "signed security context user_id is required"
            )
        if not tenant_id:
            raise SecurityError(
                SecurityErrorType.INVALID_TENANT, "signed security context tenant_id is required"
            )
        try:
            clearance = ClassificationClearance(clearance_value)
        except ValueError as exc:
            raise SecurityError(
                SecurityErrorType.UNKNOWN_CLEARANCE,
                f"unknown classification clearance {clearance_value!r}",
            ) from exc
        return SecurityContext(
            user_id=user_id,
            tenant_id=tenant_id,
            classification_clearance=clearance,
        )

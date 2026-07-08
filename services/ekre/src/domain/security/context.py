"""Security context ingress validation for every retrieval request.

Establishes the pre-ranking security gate: a retrieval request must carry a
valid :class:`SecurityContext` (identity and clearance) before any candidate is
retrieved or ranked. Enforcement against candidate metadata lands in later
sprints; S0 defines and validates the ingress contract.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from contracts.enums import ClassificationClearance
from contracts.security_context import SecurityContext
from domain.security.errors import SecurityError, SecurityErrorType
from domain.security.signing import SignedContextVerifier


class SecuritySettingsLike(Protocol):
    """Structural view of the security settings the validator depends on."""

    require_security_context: bool
    require_signed_context: bool
    context_signing_algorithm: str
    context_issuer: str
    context_audience: str
    context_leeway_seconds: int

    def context_signing_secret_value(self) -> str: ...


class SecurityContextValidator:
    """Validate and normalize the security context supplied with a request."""

    def __init__(
        self,
        *,
        require_security_context: bool,
        verifier: SignedContextVerifier | None = None,
    ) -> None:
        self._require_security_context = require_security_context
        self._verifier = verifier

    @classmethod
    def from_settings(cls, settings: SecuritySettingsLike) -> SecurityContextValidator:
        """Build a validator from the security settings."""
        verifier: SignedContextVerifier | None = None
        if settings.require_signed_context:
            verifier = SignedContextVerifier(
                secret=settings.context_signing_secret_value(),
                algorithm=settings.context_signing_algorithm,
                issuer=settings.context_issuer,
                audience=settings.context_audience,
                leeway_seconds=settings.context_leeway_seconds,
            )
        return cls(
            require_security_context=settings.require_security_context,
            verifier=verifier,
        )

    def validate(
        self,
        raw: Mapping[str, Any] | None,
        *,
        expected_tenant_id: str | None = None,
        signed_token: str | None = None,
    ) -> SecurityContext | None:
        """Validate the request security context.

        When signed contexts are required, the trusted context is derived from a
        verified ``signed_token`` (the self-asserted ``raw`` body is ignored for
        authorization); otherwise the ``raw`` payload is validated directly.
        Returns a :class:`SecurityContext` when a context is supplied, or ``None``
        when no context is present and one is not required. Raises
        :class:`SecurityError` when required but missing, when a field or
        signature is invalid, or when the context tenant conflicts with
        ``expected_tenant_id``.
        """
        if self._verifier is not None:
            return self._validate_signed(signed_token, expected_tenant_id=expected_tenant_id)
        return self._validate_unsigned(raw, expected_tenant_id=expected_tenant_id)

    def _validate_signed(
        self, signed_token: str | None, *, expected_tenant_id: str | None
    ) -> SecurityContext:
        if self._verifier is None:  # pragma: no cover - guarded by caller
            raise SecurityError(
                SecurityErrorType.MISSING_CONTEXT, "signed context verifier is not configured"
            )
        if not signed_token:
            raise SecurityError(
                SecurityErrorType.MISSING_CONTEXT,
                "a signed security context is required for every retrieval request",
            )
        context = self._verifier.verify(signed_token)
        if expected_tenant_id is not None and context.tenant_id != expected_tenant_id:
            raise SecurityError(
                SecurityErrorType.TENANT_MISMATCH,
                "security context tenant_id does not match the request tenant",
            )
        return context

    def _validate_unsigned(
        self, raw: Mapping[str, Any] | None, *, expected_tenant_id: str | None
    ) -> SecurityContext | None:
        if not raw:
            if self._require_security_context:
                raise SecurityError(
                    SecurityErrorType.MISSING_CONTEXT,
                    "a security context is required for every retrieval request",
                )
            return None

        user_id = str(raw.get("user_id", "")).strip()
        tenant_id = str(raw.get("tenant_id", "")).strip()
        clearance_value = str(raw.get("classification_clearance", "")).strip()

        if not user_id:
            raise SecurityError(
                SecurityErrorType.INVALID_USER, "security context user_id is required"
            )
        if not tenant_id:
            raise SecurityError(
                SecurityErrorType.INVALID_TENANT, "security context tenant_id is required"
            )
        if expected_tenant_id is not None and tenant_id != expected_tenant_id:
            raise SecurityError(
                SecurityErrorType.TENANT_MISMATCH,
                "security context tenant_id does not match the request tenant",
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

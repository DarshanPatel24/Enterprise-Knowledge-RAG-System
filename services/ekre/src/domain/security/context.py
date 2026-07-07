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


class SecuritySettingsLike(Protocol):
    """Structural view of the security settings the validator depends on."""

    require_security_context: bool


class SecurityContextValidator:
    """Validate and normalize the security context supplied with a request."""

    def __init__(self, *, require_security_context: bool) -> None:
        self._require_security_context = require_security_context

    @classmethod
    def from_settings(cls, settings: SecuritySettingsLike) -> SecurityContextValidator:
        """Build a validator from the security settings."""
        return cls(require_security_context=settings.require_security_context)

    def validate(
        self,
        raw: Mapping[str, Any] | None,
        *,
        expected_tenant_id: str | None = None,
    ) -> SecurityContext | None:
        """Validate the raw security context payload.

        Returns a :class:`SecurityContext` when a context is supplied, or
        ``None`` when no context is present and one is not required. Raises
        :class:`SecurityError` when required but missing, when a field is
        invalid, or when the context tenant conflicts with ``expected_tenant_id``.
        """
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

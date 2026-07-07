"""Model gateway domain errors."""

from __future__ import annotations

from enum import StrEnum


class GatewayErrorType(StrEnum):
    """Categories of model gateway failure."""

    UNKNOWN_MODEL = "unknown_model"
    MODEL_UNAVAILABLE = "model_unavailable"
    NOT_APPROVED = "not_approved"
    PROVIDER_FAILED = "provider_failed"
    FALLBACK_EXHAUSTED = "fallback_exhausted"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"  # noqa: S105 - error label, not a secret
    BUDGET_EXCEEDED = "budget_exceeded"


class GatewayError(Exception):
    """Raised when a model invocation cannot be routed, run, or governed."""

    def __init__(self, error_type: GatewayErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class ProviderInvocationError(Exception):
    """Controlled, isolable failure raised by a provider adapter."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

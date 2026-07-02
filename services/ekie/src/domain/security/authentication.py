"""Authentication: resolve credentials to a :class:`Principal` (handbook 17.4).

The deterministic, local-first default authenticates a configured anonymous
service principal so the offline pipeline runs without external identity
infrastructure. API-key authentication compares a presented key against secrets
resolved from the ephemeral secret provider using a constant-time comparison.
"""

from __future__ import annotations

import hmac
from abc import ABC, abstractmethod

from domain.security.classification import Classification
from domain.security.errors import SecurityError, SecurityErrorType
from domain.security.identity import AuthMethod, Principal, Role
from domain.security.policy import SecurityPolicy
from domain.security.secrets import SecretProvider


class Authenticator(ABC):
    """Resolves a presented credential to an authenticated principal."""

    @abstractmethod
    def authenticate(self, credential: str | None) -> Principal:
        """Return a :class:`Principal` or raise :class:`SecurityError`."""


class AnonymousAuthenticator(Authenticator):
    """Authenticate every request as the configured anonymous principal.

    Used only when authentication is not required (local-first default). The
    anonymous principal's role and clearance come from configuration, never
    hardcoded.
    """

    def __init__(self, policy: SecurityPolicy) -> None:
        self._policy = policy

    def authenticate(self, credential: str | None) -> Principal:
        """Return the configured anonymous principal."""
        return Principal(
            subject="anonymous",
            method=AuthMethod.ANONYMOUS,
            roles=frozenset({self._policy.anonymous_role}),
            clearance=self._policy.anonymous_clearance,
        )


class ApiKeyAuthenticator(Authenticator):
    """Authenticate a presented API key against a resolved secret.

    The expected key is resolved from the ephemeral secret provider (never
    stored inline) and compared in constant time to avoid timing side channels.
    """

    def __init__(
        self,
        secret_provider: SecretProvider,
        *,
        secret_name: str,
        subject: str,
        roles: frozenset[Role],
        clearance: Classification,
    ) -> None:
        self._secret_provider = secret_provider
        self._secret_name = secret_name
        self._subject = subject
        self._roles = roles
        self._clearance = clearance

    def authenticate(self, credential: str | None) -> Principal:
        """Validate ``credential`` against the configured API-key secret."""
        if not credential:
            raise SecurityError(
                SecurityErrorType.UNAUTHENTICATED,
                "API key credential is required",
            )
        expected = self._secret_provider.resolve(self._secret_name)
        if not hmac.compare_digest(credential, expected):
            raise SecurityError(
                SecurityErrorType.UNAUTHENTICATED,
                "Presented API key is invalid",
            )
        return Principal(
            subject=self._subject,
            method=AuthMethod.API_KEY,
            roles=self._roles,
            clearance=self._clearance,
        )

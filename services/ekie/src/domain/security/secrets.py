"""Secret resolution and tracking (handbook 17.8).

Secrets are resolved from an ephemeral provider and never persisted to the
control plane, object storage, or logs. Every resolved secret value is
registered with the :class:`SecretRegistry` so the logging redaction filter can
scrub it from any structured log record.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from domain.security.errors import SecurityError, SecurityErrorType


class SecretRegistry:
    """Tracks resolved secret values so they can be redacted from logs.

    The registry stores only the literal secret values (not their names) and
    exposes them to the redaction filter. It is process-local and never
    serialized.
    """

    def __init__(self) -> None:
        self._values: set[str] = set()

    def register(self, value: str) -> None:
        """Track ``value`` for redaction (ignores empty values)."""
        if value:
            self._values.add(value)

    def values(self) -> frozenset[str]:
        """Return an immutable snapshot of tracked secret values."""
        return frozenset(self._values)


class SecretMapLike(Protocol):
    """Structural type for a mapping of secret name to value."""

    def get(self, key: str, /) -> str | None: ...


class SecretProvider(ABC):
    """Resolves named secrets from an ephemeral, non-persistent backend."""

    @abstractmethod
    def resolve(self, name: str) -> str:
        """Return the secret value for ``name`` or raise :class:`SecurityError`."""


class EnvSecretProvider(SecretProvider):
    """Local-first secret provider backed by an in-memory mapping.

    Values originate from environment-backed settings (never hardcoded) and are
    injected at construction time. Every resolved value is registered for log
    redaction, satisfying the "no secrets in logs" control.
    """

    def __init__(
        self,
        secrets: SecretMapLike,
        *,
        registry: SecretRegistry | None = None,
    ) -> None:
        self._secrets = secrets
        self._registry = registry or SecretRegistry()

    @property
    def registry(self) -> SecretRegistry:
        """Return the registry tracking resolved secrets for redaction."""
        return self._registry

    def resolve(self, name: str) -> str:
        """Return the secret for ``name`` and register it for redaction."""
        value = self._secrets.get(name)
        if not value:
            raise SecurityError(
                SecurityErrorType.SECRET_UNAVAILABLE,
                f"Secret {name!r} is not available",
            )
        self._registry.register(value)
        return value

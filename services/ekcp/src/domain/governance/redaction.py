"""Secret redaction for logs (handbook 12; mirrors EKIE redaction).

Tracks resolved secret values and scrubs them, and known sensitive field names,
from every log record so credentials never reach the log stream. The registry is
primed from settings at startup.
"""

from __future__ import annotations

import logging
from typing import Final

REDACTED: Final = "***redacted***"

_SENSITIVE_KEYS: Final = frozenset(
    {
        "password",
        "secret",
        "secret_key",
        "api_key",
        "apikey",
        "token",
        "access_key",
        "authorization",
        "credential",
        "credentials",
    }
)


class SecretRegistry:
    """Tracks resolved secret values so they can be redacted from logs."""

    def __init__(self) -> None:
        self._values: set[str] = set()

    def register(self, value: str) -> None:
        """Track ``value`` for redaction (ignores empty values)."""
        if value:
            self._values.add(value)

    def values(self) -> frozenset[str]:
        """Return an immutable snapshot of tracked secret values."""
        return frozenset(self._values)


def _redact_text(text: str, values: frozenset[str]) -> str:
    for value in values:
        if value and value in text:
            text = text.replace(value, REDACTED)
    return text


class RedactionFilter(logging.Filter):
    """Scrub registered secrets and sensitive fields from log records."""

    def __init__(self, registry: SecretRegistry) -> None:
        super().__init__()
        self._registry = registry

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask secrets in the message and extra fields; always returns True."""
        values = self._registry.values()
        if isinstance(record.msg, str) and values:
            record.msg = _redact_text(record.msg, values)
        for key, value in list(record.__dict__.items()):
            if key.startswith("_"):
                continue
            if key.lower() in _SENSITIVE_KEYS:
                record.__dict__[key] = REDACTED
            elif isinstance(value, str) and values:
                record.__dict__[key] = _redact_text(value, values)
        return True


def install_log_redaction(registry: SecretRegistry) -> RedactionFilter:
    """Attach a :class:`RedactionFilter` to every root logger handler."""
    log_filter = RedactionFilter(registry)
    root = logging.getLogger()
    for handler in root.handlers:
        handler.addFilter(log_filter)
    return log_filter

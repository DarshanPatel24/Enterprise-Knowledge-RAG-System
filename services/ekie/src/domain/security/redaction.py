"""Log redaction to keep secrets out of structured logs (handbook 17.8, 17.10).

A logging filter scrubs registered secret values and common credential-bearing
field names from every log record before the JSON formatter serializes it, so
no secret is ever exposed in logs.
"""

from __future__ import annotations

import logging
from typing import Final

from domain.security.secrets import SecretRegistry

REDACTED: Final = "***redacted***"

# Field names whose values are always masked regardless of registry contents.
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


def _redact_text(text: str, values: frozenset[str]) -> str:
    """Replace any tracked secret ``values`` found in ``text``."""
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

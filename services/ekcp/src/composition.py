"""Composition root: build EKCP foundations from settings.

Wires the settings module into engine-owned domain objects (config over code).
Domain packages stay independent of the settings module; this root is the single
place that reads settings and injects dependencies. The root grows one builder
at a time as the sprint track advances.
"""

from __future__ import annotations

from config.settings import EkcpSettings
from domain.observability import build_langfuse_callbacks, configure_logging
from domain.security import SecurityContextValidator

__all__ = [
    "build_security_validator",
    "build_tracing_callbacks",
    "configure_observability",
]


def configure_observability(settings: EkcpSettings) -> None:
    """Install structured JSON logging from the observability settings."""
    configure_logging(
        service_name=settings.observability.service_name,
        log_level=settings.observability.log_level,
    )


def build_security_validator(settings: EkcpSettings) -> SecurityContextValidator:
    """Build the security context ingress validator from settings."""
    return SecurityContextValidator.from_settings(settings.security)


def build_tracing_callbacks(settings: EkcpSettings) -> list[object]:
    """Build Langfuse tracing callbacks from settings (empty when disabled)."""
    return list(build_langfuse_callbacks(settings.observability))

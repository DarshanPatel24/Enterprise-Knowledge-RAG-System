"""Observability baseline: structured logging and correlation context."""

from domain.observability.context import (
    correlation_scope,
    get_correlation_id,
    get_tenant_id,
    set_correlation_id,
    set_tenant_id,
)
from domain.observability.logging import (
    JsonLogFormatter,
    configure_logging,
    get_logger,
)

__all__ = [
    "JsonLogFormatter",
    "configure_logging",
    "correlation_scope",
    "get_correlation_id",
    "get_logger",
    "get_tenant_id",
    "set_correlation_id",
    "set_tenant_id",
]

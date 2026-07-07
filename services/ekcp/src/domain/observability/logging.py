"""Structured JSON logging baseline for EKCP.

Emits one JSON object per log record and automatically enriches every record
with the ``tenant_id``, ``correlation_id``, and ``session_id`` bound to the
current context. This is the observability substrate every conversation stage
builds on.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from domain.observability.context import (
    get_correlation_id,
    get_session_id,
    get_tenant_id,
)

_RESERVED_ATTRS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonLogFormatter(logging.Formatter):
    """Format log records as single-line JSON with correlation context."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": self._service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "tenant_id": get_tenant_id(),
            "correlation_id": get_correlation_id(),
            "session_id": get_session_id(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(service_name: str = "ekcp", log_level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    root = logging.getLogger()
    root.setLevel(log_level.upper())

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonLogFormatter(service_name=service_name))

    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that inherits the configured JSON handler."""
    return logging.getLogger(name)

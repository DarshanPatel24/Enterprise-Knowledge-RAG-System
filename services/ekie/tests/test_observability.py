"""Tests for the structured JSON logging and correlation context baseline."""

import json
import logging

from domain.observability import (
    JsonLogFormatter,
    correlation_scope,
    get_correlation_id,
    get_tenant_id,
)


def _format(record: logging.LogRecord) -> dict[str, object]:
    formatter = JsonLogFormatter(service_name="ekie")
    return json.loads(formatter.format(record))


def _make_record(message: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="ekie.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_json_formatter_emits_core_fields() -> None:
    payload = _format(_make_record("hello"))
    assert payload["level"] == "INFO"
    assert payload["service"] == "ekie"
    assert payload["message"] == "hello"
    assert "timestamp" in payload


def test_correlation_scope_binds_and_resets() -> None:
    assert get_tenant_id() is None
    with correlation_scope(tenant_id="tenant-a", correlation_id="corr-1"):
        assert get_tenant_id() == "tenant-a"
        assert get_correlation_id() == "corr-1"
        payload = _format(_make_record("scoped"))
        assert payload["tenant_id"] == "tenant-a"
        assert payload["correlation_id"] == "corr-1"
    assert get_tenant_id() is None
    assert get_correlation_id() is None

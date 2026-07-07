"""Correlation context propagation for observability.

Binds ``tenant_id``, ``correlation_id``, and ``query_id`` to the current
execution scope so every log record and trace can carry them without threading
arguments through every function. Values are stored in
:class:`contextvars.ContextVar` objects, which are safe across ``async`` tasks
and threads.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

_tenant_id: ContextVar[str | None] = ContextVar("ekre_tenant_id", default=None)
_correlation_id: ContextVar[str | None] = ContextVar("ekre_correlation_id", default=None)
_query_id: ContextVar[str | None] = ContextVar("ekre_query_id", default=None)


def get_tenant_id() -> str | None:
    """Return the tenant id bound to the current context, if any."""
    return _tenant_id.get()


def get_correlation_id() -> str | None:
    """Return the correlation id bound to the current context, if any."""
    return _correlation_id.get()


def get_query_id() -> str | None:
    """Return the query id bound to the current context, if any."""
    return _query_id.get()


def set_tenant_id(tenant_id: str | None) -> Token[str | None]:
    """Bind ``tenant_id`` to the current context and return a reset token."""
    return _tenant_id.set(tenant_id)


def set_correlation_id(correlation_id: str | None) -> Token[str | None]:
    """Bind ``correlation_id`` to the current context and return a reset token."""
    return _correlation_id.set(correlation_id)


def set_query_id(query_id: str | None) -> Token[str | None]:
    """Bind ``query_id`` to the current context and return a reset token."""
    return _query_id.set(query_id)


@contextmanager
def correlation_scope(
    *,
    tenant_id: str | None = None,
    correlation_id: str | None = None,
    query_id: str | None = None,
) -> Iterator[None]:
    """Bind correlation identifiers for the duration of the ``with`` block."""
    tenant_token = _tenant_id.set(tenant_id)
    correlation_token = _correlation_id.set(correlation_id)
    query_token = _query_id.set(query_id)
    try:
        yield
    finally:
        _query_id.reset(query_token)
        _correlation_id.reset(correlation_token)
        _tenant_id.reset(tenant_token)

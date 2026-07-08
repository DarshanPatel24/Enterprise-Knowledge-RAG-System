"""Tracing seam: build Langfuse callbacks when tracing is enabled.

The offline default returns no callbacks so the deterministic path never loads
Langfuse. When enabled, the callback handler is configured from settings and
must point to the local self-hosted instance only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydantic import SecretStr


class TracingSettingsLike(Protocol):
    """Structural view of the observability settings needed for tracing."""

    langfuse_enabled: bool
    langfuse_url: str
    langfuse_public_key: str
    langfuse_secret_key: SecretStr


def build_langfuse_callbacks(settings: TracingSettingsLike) -> list[Any]:
    """Return Langfuse callback handlers, or an empty list when disabled.

    Imports are lazy so the offline path never requires ``langfuse``. Any import
    or construction failure degrades gracefully to no tracing.
    """
    if not settings.langfuse_enabled:
        return []
    try:
        from langfuse.callback import CallbackHandler
    except ImportError:
        return []
    handler = CallbackHandler(
        host=settings.langfuse_url,
        public_key=settings.langfuse_public_key or None,
        secret_key=settings.langfuse_secret_key.get_secret_value() or None,
    )
    callbacks: Sequence[Any] = [handler]
    return list(callbacks)

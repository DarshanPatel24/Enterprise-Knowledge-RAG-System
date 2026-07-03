"""Optional Langfuse tracing for the LangGraph orchestration runner.

Tracing is self-hosted and disabled by default (local-first). The Langfuse
client is imported lazily so the offline path stays dependency-free; when the
package is absent the orchestrator degrades to structured-log tracing, which
already carries ``tenant_id`` and ``correlation_id`` from the request context.
"""

from __future__ import annotations

from typing import Protocol

from domain.observability import get_logger

logger = get_logger("ekie.orchestration.tracing")


class LangfuseSettingsLike(Protocol):
    """Structural type for environment-backed Langfuse settings."""

    langfuse_enabled: bool
    langfuse_host: str
    langfuse_public_key: str
    langfuse_secret_key: str


def build_langfuse_callbacks(settings: LangfuseSettingsLike) -> list[object]:
    """Return LangChain callbacks for Langfuse, or an empty list when disabled.

    Returns an empty list when tracing is disabled or the ``langfuse`` package
    is not installed, so callers can always pass the result to the graph config.
    """
    if not settings.langfuse_enabled:
        return []
    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        try:
            from langfuse.callback import CallbackHandler  # langfuse <2.x fallback
        except ImportError:
            logger.warning(
                "langfuse_unavailable",
                extra={"detail": "langfuse not installed; falling back to log tracing"},
            )
            return []

    # langfuse v2+ reads credentials from LANGFUSE_* environment variables.
    # Inject them from settings so operators only configure services/ekie/.env.
    import os
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)

    handler = CallbackHandler()
    return [handler]

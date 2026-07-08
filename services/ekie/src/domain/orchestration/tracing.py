"""Optional Langfuse tracing for the LangGraph orchestration runner.

Tracing is self-hosted and disabled by default (local-first). The Langfuse
client is imported lazily so the offline path stays dependency-free; when the
package is absent the orchestrator degrades to structured-log tracing, which
already carries ``tenant_id`` and ``correlation_id`` from the request context.

Uses the direct Langfuse Python SDK (no LangChain callback dependency) so it
works with any version of langchain.
"""

from __future__ import annotations

from typing import Any, Protocol

from domain.observability import get_logger

logger = get_logger("ekie.orchestration.tracing")


class LangfuseSettingsLike(Protocol):
    """Structural type for environment-backed Langfuse settings."""

    langfuse_enabled: bool
    langfuse_url: str
    langfuse_public_key: str
    langfuse_secret_key: str


def build_langfuse_client(
    settings: LangfuseSettingsLike,
) -> Any | None:  # noqa: ANN401 - returns opaque third-party client
    """Return a Langfuse client for direct trace creation, or None when disabled.

    Uses ``langfuse.Langfuse`` directly — no LangChain callback dependency.
    This works with any version of langchain and any langfuse v2 release.
    """
    if not settings.langfuse_enabled:
        return None
    if not settings.langfuse_public_key:
        logger.warning(
            "langfuse_unavailable",
            extra={"detail": "EKIE_OBSERVABILITY__LANGFUSE_PUBLIC_KEY not set"},
        )
        return None
    try:
        from langfuse import Langfuse
    except ImportError:
        logger.warning(
            "langfuse_unavailable",
            extra={
                "detail": "langfuse package not installed; "
                "run: pip install 'langfuse>=2.0,<3.0'"
            },
        )
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_url,
    )


# Backward-compatibility shim — the old callback list approach is replaced
# by direct trace creation in the runner; this always returns an empty list
# so existing call sites that pass it as `tracer_callbacks` keep working.
def build_langfuse_callbacks(settings: LangfuseSettingsLike) -> list[object]:
    """Legacy shim: callbacks approach replaced by direct tracing.

    Returns an empty list; callers should switch to :func:`build_langfuse_client`.
    """
    return []

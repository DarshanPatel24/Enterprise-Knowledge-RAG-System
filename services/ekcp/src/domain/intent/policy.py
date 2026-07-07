"""Intent policy: confidence threshold and classification vocabulary.

The policy is injected into the classifier and gate so no thresholds or keyword
tables are hardcoded in engine logic. Signal tables are ordered so the first
match wins, keeping classification deterministic.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

# Ordered intent signal table: the first intent whose keywords match wins.
_INTENT_SIGNALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("workflow", ("workflow", "process", "approve", "approval", "multi-step", "pipeline")),
    ("analysis", ("compare", "summarize", "analyze", "difference", "trend", "synthesize")),
    ("agent_request", ("agent", "delegate", "assign to", "hand off")),
    (
        "task",
        ("create", "generate", "build", "send", "update", "delete", "run", "execute", "schedule"),
    ),
    ("collaboration", ("let's", "brainstorm", "discuss", "work through", "collaborate")),
)

# Personal-scope signals route to conversation/user memory.
_PERSONAL_SIGNALS: tuple[str, ...] = (
    "we discuss",
    "we talked",
    "what did we",
    "our conversation",
    "yesterday",
    "earlier",
    "last time",
    "previously",
    "remember",
    "you said",
    "my preference",
    "recap",
    "remind me",
)

# Organizational-scope signals route to enterprise knowledge (EKRE).
_ORGANIZATIONAL_SIGNALS: tuple[str, ...] = (
    "policy",
    "company",
    "organization",
    "documentation",
    "docs",
    "guide",
    "manual",
    "procedure",
    "compliance",
    "standard",
    "regulation",
    "how do i",
    "what is the",
    "handbook",
)


class IntentSettingsLike(Protocol):
    """Structural view of the intent settings the policy depends on."""

    confidence_threshold: float
    default_language: str


class IntentPolicy(BaseModel):
    """Immutable intent policy resolved from settings."""

    model_config = ConfigDict(frozen=True)

    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    default_language: str = "en"

    @classmethod
    def from_settings(cls, settings: IntentSettingsLike) -> IntentPolicy:
        """Build the intent policy from the intent settings."""
        return cls(
            confidence_threshold=settings.confidence_threshold,
            default_language=settings.default_language,
        )

    def intent_signals(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Return the ordered intent signal table."""
        return _INTENT_SIGNALS

    def personal_signals(self) -> tuple[str, ...]:
        """Return the personal-scope signal phrases."""
        return _PERSONAL_SIGNALS

    def organizational_signals(self) -> tuple[str, ...]:
        """Return the organizational-scope signal phrases."""
        return _ORGANIZATIONAL_SIGNALS

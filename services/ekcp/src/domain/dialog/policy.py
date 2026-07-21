"""Dialog context policy and its settings protocol.

The policy is deterministic and injected from settings so no threshold or budget
is hardcoded in the classification and rewriting logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DialogSettingsLike(Protocol):
    """Structural view of the dialog settings the policy needs."""

    history_max_turns: int
    history_token_budget: int
    chars_per_token: int
    topic_overlap_threshold: float
    clarify_confidence_threshold: float
    enable_clarification: bool
    max_search_query_chars: int


@dataclass(frozen=True)
class DialogPolicy:
    """Immutable thresholds and budgets for turn classification and rewriting."""

    history_max_turns: int
    history_token_budget: int
    chars_per_token: int
    topic_overlap_threshold: float
    clarify_confidence_threshold: float
    enable_clarification: bool
    max_search_query_chars: int

    @classmethod
    def from_settings(cls, settings: DialogSettingsLike) -> DialogPolicy:
        """Build the policy from the dialog settings."""
        return cls(
            history_max_turns=settings.history_max_turns,
            history_token_budget=settings.history_token_budget,
            chars_per_token=settings.chars_per_token,
            topic_overlap_threshold=settings.topic_overlap_threshold,
            clarify_confidence_threshold=settings.clarify_confidence_threshold,
            enable_clarification=settings.enable_clarification,
            max_search_query_chars=settings.max_search_query_chars,
        )

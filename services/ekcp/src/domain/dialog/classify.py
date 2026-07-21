"""Deterministic turn classifier.

Classifies each incoming message relative to the conversation so far, ordered
so explicit references win over ambiguity gating: clarification reply ->
follow-up -> clarification needed -> topical follow-up -> fresh. Ambiguity is
judged with the existing intent classifier's confidence, gated by a
conservative threshold so only clearly vague messages are sent back for
clarification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.dialog.errors import DialogError, DialogErrorType
from domain.dialog.models import CLARIFICATION_PROMPT, TurnType
from domain.dialog.signals import (
    has_follow_up_signal,
    last_assistant_message,
    topic_overlap,
)
from domain.intent.errors import IntentError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from domain.dialog.models import DialogMessage
    from domain.dialog.policy import DialogPolicy
    from domain.intent.classifier import IntentClassifier

# The intent classifier rejects overly long input; skip ambiguity gating above
# this length and treat such a message as a substantive (non-vague) question.
_MAX_CLARIFY_CHARS = 8000


class TurnClassifier:
    """Map a message plus prior turns to a :class:`TurnType` with a rationale."""

    def __init__(self, policy: DialogPolicy, intent_classifier: IntentClassifier) -> None:
        self._policy = policy
        self._intent = intent_classifier

    def classify(
        self, message: str, history: Sequence[DialogMessage]
    ) -> tuple[TurnType, str]:
        """Return the turn type and a short human-readable rationale."""
        text = message.strip()
        if not text:
            raise DialogError(DialogErrorType.EMPTY_MESSAGE, "message must not be empty")

        if history and last_assistant_message(history) == CLARIFICATION_PROMPT:
            return (
                TurnType.CLARIFICATION_REPLY,
                "the prior assistant turn asked for clarification",
            )

        if history and has_follow_up_signal(text):
            return (
                TurnType.FOLLOW_UP,
                "message refers back to the prior turn (anaphora or continuation)",
            )

        if self._policy.enable_clarification and self._needs_clarification(text):
            return (
                TurnType.CLARIFICATION_NEEDED,
                "message is too ambiguous to answer confidently",
            )

        if history and topic_overlap(text, history) >= self._policy.topic_overlap_threshold:
            return (TurnType.FOLLOW_UP, "message continues the current topic")

        return (TurnType.FRESH, "self-contained new question")

    def _needs_clarification(self, text: str) -> bool:
        """Return whether the message is vague enough to warrant a clarification."""
        if len(text) > _MAX_CLARIFY_CHARS:
            return False
        try:
            classification = self._intent.classify(text)
        except IntentError:
            return False
        return classification.confidence < self._policy.clarify_confidence_threshold

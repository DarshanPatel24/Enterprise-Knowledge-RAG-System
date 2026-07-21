"""Dialog context engine: the single entry point the chat path calls per turn.

Composes deterministic turn classification, query rewriting, and history pruning
into one :class:`TurnDecision`. Optional LLM condensing is injected and used only
for follow-ups when enabled; everything else is deterministic and offline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.dialog.history import prune_history
from domain.dialog.models import CLARIFICATION_PROMPT, TurnDecision, TurnType
from domain.dialog.rewrite import build_search_query

if TYPE_CHECKING:
    from collections.abc import Sequence

    from domain.dialog.classify import TurnClassifier
    from domain.dialog.condense import QuestionCondenser
    from domain.dialog.models import DialogMessage
    from domain.dialog.policy import DialogPolicy


class DialogContextEngine:
    """Decide how to handle one incoming message given the conversation so far."""

    def __init__(
        self,
        policy: DialogPolicy,
        classifier: TurnClassifier,
        *,
        condenser: QuestionCondenser | None = None,
    ) -> None:
        self._policy = policy
        self._classifier = classifier
        self._condenser = condenser

    def decide(self, message: str, history: Sequence[DialogMessage]) -> TurnDecision:
        """Return the :class:`TurnDecision` for ``message`` and prior ``history``."""
        turns = tuple(history)
        turn_type, rationale = self._classifier.classify(message, turns)

        if turn_type is TurnType.CLARIFICATION_NEEDED:
            return TurnDecision(
                turn_type=turn_type,
                search_query=message.strip(),
                history=(),
                clarification_prompt=CLARIFICATION_PROMPT,
                rationale=rationale,
            )

        search_query = build_search_query(
            message, turns, turn_type, policy=self._policy, condenser=self._condenser
        )
        kept = prune_history(turns, turn_type, self._policy)
        return TurnDecision(
            turn_type=turn_type,
            search_query=search_query,
            history=kept,
            rationale=rationale,
        )

"""Build the retrieval query for a turn.

Fresh questions and clarification requests search on the message as typed.
Follow-ups and clarification replies are contextualized so retrieval sees a
standalone query: an optional LLM condenser first (when enabled), otherwise a
deterministic rewrite that prepends the prior user question.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.dialog.models import TurnType
from domain.dialog.signals import last_user_message

if TYPE_CHECKING:
    from collections.abc import Sequence

    from domain.dialog.condense import QuestionCondenser
    from domain.dialog.models import DialogMessage
    from domain.dialog.policy import DialogPolicy


def build_search_query(
    message: str,
    history: Sequence[DialogMessage],
    turn_type: TurnType,
    *,
    policy: DialogPolicy,
    condenser: QuestionCondenser | None = None,
) -> str:
    """Return the query retrieval should use for this turn."""
    text = message.strip()
    if turn_type in (TurnType.FRESH, TurnType.CLARIFICATION_NEEDED):
        return text

    if condenser is not None and condenser.enabled:
        condensed = condenser.condense(text, history)
        if condensed:
            return _truncate(condensed, policy.max_search_query_chars)

    prior = last_user_message(history)
    if not prior:
        return text
    return _truncate(f"{prior} {text}".strip(), policy.max_search_query_chars)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()

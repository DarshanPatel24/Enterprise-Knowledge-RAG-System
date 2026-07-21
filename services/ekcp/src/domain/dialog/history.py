"""History pruning and rendering for the generation prompt.

A fresh question carries no history (saving tokens); follow-ups and clarification
replies carry the most recent turns within a token budget so a long conversation
never overflows the model context window.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.context.tokens import estimate_tokens
from domain.dialog.models import TurnType

if TYPE_CHECKING:
    from collections.abc import Sequence

    from domain.dialog.models import DialogMessage
    from domain.dialog.policy import DialogPolicy


def prune_history(
    history: Sequence[DialogMessage], turn_type: TurnType, policy: DialogPolicy
) -> tuple[DialogMessage, ...]:
    """Return the prior turns to carry into generation for ``turn_type``.

    Fresh and clarification-needed turns carry nothing. Otherwise the most recent
    turns are kept, newest first, until the token budget is reached (always
    keeping at least the single most recent turn).
    """
    if turn_type in (TurnType.FRESH, TurnType.CLARIFICATION_NEEDED):
        return ()

    recent = [turn for turn in history if turn.content.strip()][-policy.history_max_turns :]
    kept: list[DialogMessage] = []
    used = 0
    for turn in reversed(recent):
        cost = estimate_tokens(turn.content, chars_per_token=policy.chars_per_token)
        if kept and used + cost > policy.history_token_budget:
            break
        used += cost
        kept.append(turn)
    kept.reverse()
    return tuple(kept)


def render_history(history: Sequence[DialogMessage]) -> str:
    """Render prior turns as a compact ``Role: text`` transcript."""
    if not history:
        return ""
    lines = [
        f"{'User' if turn.role == 'user' else 'Assistant'}: {' '.join(turn.content.split())}"
        for turn in history
    ]
    return "\n".join(lines)

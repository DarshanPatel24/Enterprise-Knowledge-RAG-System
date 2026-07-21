"""Dialog turn models: the decision the streaming chat path acts on.

A :class:`TurnDecision` tells the chat pipeline, for one incoming message,
whether to answer fresh, treat it as a follow-up (with a retrieval query
rewritten from prior turns), ask for clarification, or link a clarification
reply back to the original question --- and exactly which prior turns to carry
into generation. The decision is deterministic and explainable.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TurnType(StrEnum):
    """How the incoming message relates to the conversation so far."""

    FRESH = "fresh"
    FOLLOW_UP = "follow_up"
    CLARIFICATION_NEEDED = "clarification_needed"
    CLARIFICATION_REPLY = "clarification_reply"


# The exact clarification text emitted for a CLARIFICATION_NEEDED turn. It is a
# module constant (not inlined per call site) so the classifier can also
# recognize a prior assistant clarification when detecting a CLARIFICATION_REPLY.
CLARIFICATION_PROMPT = (
    "I want to make sure I answer the right thing. Could you add a little more "
    "detail -- for example the product, feature, or task you mean?"
)


class DialogMessage(BaseModel):
    """A single prior conversation turn used for context decisions."""

    model_config = ConfigDict(frozen=True)

    role: str = Field(min_length=1)
    content: str = Field(min_length=1)


class TurnDecision(BaseModel):
    """Deterministic decision for one incoming message.

    ``search_query`` is what retrieval should use (rewritten from prior turns for
    follow-ups and clarification replies; the original message otherwise).
    ``history`` is the pruned, token-budgeted set of prior turns to carry into
    generation (empty for a fresh question, to save tokens). When
    ``turn_type`` is ``CLARIFICATION_NEEDED`` the pipeline should emit
    ``clarification_prompt`` and skip retrieval and generation entirely.
    """

    model_config = ConfigDict(frozen=True)

    turn_type: TurnType
    search_query: str
    history: tuple[DialogMessage, ...] = ()
    clarification_prompt: str = ""
    rationale: str = ""

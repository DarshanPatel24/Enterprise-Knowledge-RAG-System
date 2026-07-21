"""Dialog context: deterministic multi-turn handling for the streaming chat path.

Decides, per incoming message, whether to answer fresh, treat it as a follow-up
(rewriting the retrieval query from prior turns), ask for clarification, or link
a clarification reply back to the original question -- and which prior turns to
carry into generation. Deterministic and offline by default; an optional local
LLM condenser refines follow-up queries when enabled.
"""

from __future__ import annotations

from domain.dialog.classify import TurnClassifier
from domain.dialog.condense import QuestionCondenser
from domain.dialog.engine import DialogContextEngine
from domain.dialog.errors import DialogError, DialogErrorType
from domain.dialog.history import prune_history, render_history
from domain.dialog.models import (
    CLARIFICATION_PROMPT,
    DialogMessage,
    TurnDecision,
    TurnType,
)
from domain.dialog.policy import DialogPolicy, DialogSettingsLike
from domain.dialog.rewrite import build_search_query

__all__ = [
    "CLARIFICATION_PROMPT",
    "DialogContextEngine",
    "DialogError",
    "DialogErrorType",
    "DialogMessage",
    "DialogPolicy",
    "DialogSettingsLike",
    "QuestionCondenser",
    "TurnClassifier",
    "TurnDecision",
    "TurnType",
    "build_search_query",
    "prune_history",
    "render_history",
]

"""Deterministic lexical signals for turn classification and query rewriting.

Pure functions over message text and prior turns: tokenization, distinctive
(content) terms, follow-up/anaphora detection, topic overlap, and helpers that
locate the prior user question. No model calls; fully reproducible offline.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from domain.dialog.models import DialogMessage

_WORD = re.compile(r"[a-z0-9]+")

# Function words that carry no topical meaning; dropped before overlap/keyword
# work so only content-bearing terms decide topic continuity.
_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "if", "then", "of", "to", "in", "on",
        "for", "with", "is", "are", "was", "were", "be", "been", "being", "do",
        "does", "did", "how", "what", "why", "when", "where", "who", "which", "can",
        "could", "should", "would", "will", "i", "you", "we", "it", "this", "that",
        "these", "those", "me", "my", "our", "your", "at", "by", "from", "as",
        "about", "into", "please", "tell", "show", "give", "need", "want", "get",
        "use", "using", "there", "here", "also", "so", "not",
    }
)

# Single-word anaphora / deixis. Because these words also appear in fresh
# questions, they only signal a follow-up in a short (elliptical) message.
_ANAPHORA_WORDS: frozenset[str] = frozenset(
    {"it", "its", "them", "they", "one", "that", "this", "these", "those"}
)

# Multi-word references that reliably point at a prior turn regardless of length.
_ANAPHORA_PHRASES: tuple[str, ...] = (
    "the former", "the latter", "the first", "the second", "the third",
    "the previous", "the above", "the same", "the other",
)

# Leading discourse markers that signal a continuation of the prior turn.
_FOLLOW_UP_PREFIXES: tuple[str, ...] = (
    "and ", "also ", "what about", "how about", "then ", "next ", "plus ",
    "in addition", "furthermore", "besides", "additionally", "and what",
)

# A short message is treated as potentially elliptical (leaning on prior turns).
_ELLIPSIS_MAX_TOKENS = 8


def tokenize(text: str) -> list[str]:
    """Return lowercase alphanumeric word tokens."""
    return _WORD.findall(text.lower())


def distinctive_terms(text: str) -> frozenset[str]:
    """Return content-bearing terms (stopwords and single characters removed)."""
    return frozenset(
        token for token in tokenize(text) if token not in _STOP_WORDS and len(token) > 1
    )


def has_follow_up_signal(message: str) -> bool:
    """Return whether ``message`` explicitly refers back to the conversation."""
    lowered = message.strip().lower()
    if any(lowered.startswith(prefix) for prefix in _FOLLOW_UP_PREFIXES):
        return True
    if any(phrase in lowered for phrase in _ANAPHORA_PHRASES):
        return True
    tokens = tokenize(lowered)
    return len(tokens) <= _ELLIPSIS_MAX_TOKENS and any(
        token in _ANAPHORA_WORDS for token in tokens
    )


def topic_overlap(message: str, history: Sequence[DialogMessage]) -> float:
    """Return the fraction of the message's distinctive terms seen in prior user turns."""
    current = distinctive_terms(message)
    if not current:
        return 0.0
    prior: set[str] = set()
    for turn in history:
        if turn.role == "user":
            prior |= distinctive_terms(turn.content)
    if not prior:
        return 0.0
    return len(current & prior) / len(current)


def last_user_message(history: Sequence[DialogMessage]) -> str:
    """Return the most recent non-empty user turn, or an empty string."""
    for turn in reversed(history):
        if turn.role == "user" and turn.content.strip():
            return turn.content.strip()
    return ""


def last_assistant_message(history: Sequence[DialogMessage]) -> str:
    """Return the most recent non-empty assistant turn, or an empty string."""
    for turn in reversed(history):
        if turn.role == "assistant" and turn.content.strip():
            return turn.content.strip()
    return ""

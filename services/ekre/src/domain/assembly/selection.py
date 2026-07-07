"""Context selection within the token budget (handbook Chapter 26.7).

Selects ranked knowledge objects into the context window, in rank order, honoring
the token budget, object cap, relevance threshold, and content deduplication.
Selection never changes knowledge object content. The result is deterministic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from domain.assembly.policy import AssemblyPolicy
from domain.assembly.tokens import estimate_tokens, optimize_content
from domain.ranking.models import RankedKnowledgeObject


@dataclass(frozen=True)
class SelectedContext:
    """A ranked object selected for context, with its optimized content/tokens."""

    ranked: RankedKnowledgeObject
    content: str
    tokens: int


@dataclass(frozen=True)
class SelectionResult:
    """The outcome of context selection, including drop accounting."""

    selected: tuple[SelectedContext, ...]
    total_tokens: int
    dropped_for_budget: int
    dropped_duplicates: int
    dropped_below_relevance: int


class ContextSelector:
    """Selects ranked objects into the context window within the budget."""

    def __init__(self, policy: AssemblyPolicy) -> None:
        self._policy = policy

    def select(self, objects: Sequence[RankedKnowledgeObject]) -> SelectionResult:
        """Select objects in rank order within the token and object budgets."""
        selected: list[SelectedContext] = []
        seen_content: set[str] = set()
        total_tokens = 0
        dropped_budget = 0
        dropped_dupes = 0
        dropped_relevance = 0

        for obj in objects:
            if obj.composite_score < self._policy.min_relevance:
                dropped_relevance += 1
                continue
            content = optimize_content(
                obj.knowledge_object.content,
                normalize_whitespace=self._policy.normalize_whitespace,
            )
            if self._policy.dedupe_content and content in seen_content:
                dropped_dupes += 1
                continue
            if len(selected) >= self._policy.max_objects:
                dropped_budget += 1
                continue
            tokens = estimate_tokens(content, chars_per_token=self._policy.chars_per_token)
            # Always admit at least one object even if it exceeds the budget.
            if selected and total_tokens + tokens > self._policy.max_context_tokens:
                dropped_budget += 1
                continue
            selected.append(SelectedContext(ranked=obj, content=content, tokens=tokens))
            seen_content.add(content)
            total_tokens += tokens

        return SelectionResult(
            selected=tuple(selected),
            total_tokens=total_tokens,
            dropped_for_budget=dropped_budget,
            dropped_duplicates=dropped_dupes,
            dropped_below_relevance=dropped_relevance,
        )

"""Intent Classification Engine (handbook Chapter 10).

Determines *why* a retrieval is being performed and recommends the retrieval
profile and candidate count. Classification is deterministic: the same query
against the same policy always yields the same intent.
"""

from __future__ import annotations

from domain.query.models import (
    IntentClassification,
    QueryComplexity,
    QueryUnderstanding,
    RetrievalIntent,
    RetrievalProfile,
)
from domain.query.policy import QueryPolicy

# Ordered signal table: the first intent whose keywords match wins, so the
# mapping is deterministic and reviewable. Keywords are matched on word
# boundaries against the normalized, lower-cased query.
_INTENT_SIGNALS: tuple[tuple[RetrievalIntent, tuple[str, ...]], ...] = (
    (RetrievalIntent.COMPARISON, ("compare", "versus", " vs ", "difference between")),
    (RetrievalIntent.ANALYTICAL, ("changes between", "trend", "over time", "correlation")),
    (RetrievalIntent.COMPLIANCE, ("gdpr", "compliance", "regulation", "policy regarding", "audit")),
    (RetrievalIntent.RESEARCH, ("everything about", "all about", "everything related")),
    (RetrievalIntent.DISCOVERY, ("best practice", "how to", "recommendation", "ideas for")),
    (RetrievalIntent.NAVIGATION, ("open", "latest", "show me", "go to", "find the")),
    (RetrievalIntent.EXACT_LOOKUP, ("policy", "guide", "manual", "handbook", "definition of")),
)

# Retrieval profile recommended for each intent.
_INTENT_PROFILE: dict[RetrievalIntent, RetrievalProfile] = {
    RetrievalIntent.EXACT_LOOKUP: RetrievalProfile.PRECISION,
    RetrievalIntent.NAVIGATION: RetrievalProfile.PRECISION,
    RetrievalIntent.RESEARCH: RetrievalProfile.RECALL,
    RetrievalIntent.DISCOVERY: RetrievalProfile.RECALL,
    RetrievalIntent.COMPARISON: RetrievalProfile.BALANCED,
    RetrievalIntent.ANALYTICAL: RetrievalProfile.BALANCED,
    RetrievalIntent.COMPLIANCE: RetrievalProfile.COMPLIANCE,
    RetrievalIntent.AI_CONTEXT: RetrievalProfile.BALANCED,
}

# Recall/precision expectation per profile.
_PROFILE_EXPECTATION: dict[RetrievalProfile, tuple[float, float]] = {
    RetrievalProfile.PRECISION: (0.4, 0.9),
    RetrievalProfile.RECALL: (0.9, 0.4),
    RetrievalProfile.BALANCED: (0.7, 0.7),
    RetrievalProfile.COMPLIANCE: (0.8, 0.8),
    RetrievalProfile.PERFORMANCE: (0.5, 0.6),
}

_DEFAULT_INTENT = RetrievalIntent.RESEARCH


class IntentClassificationEngine:
    """Deterministic rule-based retrieval intent classifier."""

    def __init__(self, policy: QueryPolicy) -> None:
        self._policy = policy

    def classify(self, understanding: QueryUnderstanding) -> IntentClassification:
        """Classify the retrieval intent for a Structured Query Model v1."""
        haystack = f" {understanding.normalized_query.lower()} "
        intent, matched = self._match_intent(haystack)
        secondary = self._secondary_intents(haystack, intent)
        profile = _INTENT_PROFILE[intent]
        expected_recall, expected_precision = _PROFILE_EXPECTATION[profile]
        complexity = self._complexity(understanding)
        confidence = self._confidence(matched, complexity)

        warnings: list[str] = []
        if not matched:
            warnings.append("no explicit intent signal; defaulted to research")

        return IntentClassification(
            intent=intent,
            confidence=confidence,
            complexity=complexity,
            expected_recall=expected_recall,
            expected_precision=expected_precision,
            suggested_profile=profile,
            suggested_candidate_count=self._policy.candidate_count(profile),
            secondary_intents=secondary,
            warnings=tuple(warnings),
        )

    def _match_intent(self, haystack: str) -> tuple[RetrievalIntent, bool]:
        for intent, keywords in _INTENT_SIGNALS:
            if any(keyword in haystack for keyword in keywords):
                return intent, True
        return _DEFAULT_INTENT, False

    def _secondary_intents(
        self, haystack: str, primary: RetrievalIntent
    ) -> tuple[RetrievalIntent, ...]:
        secondary: list[RetrievalIntent] = []
        for intent, keywords in _INTENT_SIGNALS:
            if intent is primary:
                continue
            if any(keyword in haystack for keyword in keywords):
                secondary.append(intent)
        return tuple(secondary)

    def _complexity(self, understanding: QueryUnderstanding) -> QueryComplexity:
        token_count = len(understanding.normalized_query.split())
        signal_count = len(understanding.entities) + len(understanding.metadata_filters)
        if token_count <= 4 and signal_count <= 1:
            return QueryComplexity.SIMPLE
        if token_count >= 12 or signal_count >= 3:
            return QueryComplexity.COMPLEX
        return QueryComplexity.MODERATE

    def _confidence(self, matched: bool, complexity: QueryComplexity) -> float:
        base = 0.85 if matched else 0.5
        if complexity is QueryComplexity.COMPLEX:
            base -= 0.1
        return max(0.0, min(1.0, round(base, 3)))

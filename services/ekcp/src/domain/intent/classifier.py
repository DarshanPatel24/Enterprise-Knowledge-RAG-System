"""Deterministic intent classifier and the intent-before-execution gate.

The classifier maps a user message to an :class:`IntentClassification` using
ordered keyword tables (first match wins). The gate applies the confidence
policy: when confidence is below the threshold it requests clarification and
blocks execution rather than acting on ambiguous input.
"""

from __future__ import annotations

from domain.intent.errors import IntentError, IntentErrorType
from domain.intent.models import (
    IntentClassification,
    IntentComplexity,
    IntentDecision,
    IntentScope,
    IntentType,
    RoutingTarget,
)
from domain.intent.policy import IntentPolicy

_QUESTION_MARKERS: tuple[str, ...] = ("what", "why", "how", "when", "where", "who", "which", "?")
_MAX_QUERY_CHARS = 8000

_CLARIFICATION_INTERPRETATIONS: tuple[str, ...] = (
    "ask about enterprise knowledge or policy",
    "ask about our previous conversation",
    "request an action or task to be performed",
)


class IntentClassifier:
    """Classify a user message into a deterministic intent classification."""

    def __init__(self, policy: IntentPolicy) -> None:
        self._policy = policy

    def classify(self, message: str) -> IntentClassification:
        """Return the intent classification for ``message``."""
        text = message.strip()
        if not text:
            raise IntentError(IntentErrorType.EMPTY_QUERY, "message must not be empty")
        if len(text) > _MAX_QUERY_CHARS:
            raise IntentError(
                IntentErrorType.QUERY_TOO_LONG,
                f"message exceeds {_MAX_QUERY_CHARS} characters",
            )

        lowered = text.lower()
        tokens = lowered.split()

        intent, intent_matched = self._detect_intent(lowered)
        scope, scope_matched, warnings = self._detect_scope(lowered)
        complexity = self._complexity(len(tokens))
        confidence = self._confidence(
            intent_matched=intent_matched,
            scope_matched=scope_matched,
            token_count=len(tokens),
            scope=scope,
        )
        requires_clarification = confidence < self._policy.confidence_threshold

        clarification_prompt = ""
        interpretations: tuple[str, ...] = ()
        if requires_clarification:
            clarification_prompt = (
                "I want to make sure I understand. Could you clarify what you would "
                "like me to do?"
            )
            interpretations = _CLARIFICATION_INTERPRETATIONS

        return IntentClassification(
            intent=intent,
            scope=scope,
            complexity=complexity,
            confidence=round(confidence, 4),
            requires_clarification=requires_clarification,
            clarification_prompt=clarification_prompt,
            suggested_interpretations=interpretations,
            warnings=warnings,
        )

    def _detect_intent(self, lowered: str) -> tuple[IntentType, bool]:
        for name, keywords in self._policy.intent_signals():
            if any(keyword in lowered for keyword in keywords):
                return IntentType(name), True
        if any(marker in lowered for marker in _QUESTION_MARKERS):
            return IntentType.QUESTION, True
        return IntentType.QUESTION, False

    def _detect_scope(self, lowered: str) -> tuple[IntentScope, bool, tuple[str, ...]]:
        personal = any(signal in lowered for signal in self._policy.personal_signals())
        organizational = any(
            signal in lowered for signal in self._policy.organizational_signals()
        )
        if personal and organizational:
            return IntentScope.MIXED, True, ("message spans personal and organizational scope",)
        if personal:
            return IntentScope.PERSONAL, True, ()
        if organizational:
            return IntentScope.ORGANIZATIONAL, True, ()
        return IntentScope.UNKNOWN, False, ()

    @staticmethod
    def _complexity(token_count: int) -> IntentComplexity:
        if token_count <= 4:
            return IntentComplexity.SIMPLE
        if token_count <= 16:
            return IntentComplexity.MODERATE
        return IntentComplexity.COMPLEX

    @staticmethod
    def _confidence(
        *, intent_matched: bool, scope_matched: bool, token_count: int, scope: IntentScope
    ) -> float:
        confidence = 0.5
        if intent_matched:
            confidence += 0.25
        if scope_matched:
            confidence += 0.2
        if token_count >= 4:
            confidence += 0.05
        if token_count < 2 and not intent_matched:
            confidence = 0.2
        if scope is IntentScope.MIXED:
            confidence -= 0.1
        return max(0.0, min(confidence, 0.99))


class IntentGate:
    """Apply the confidence policy: allow execution or request clarification."""

    def __init__(self, classifier: IntentClassifier) -> None:
        self._classifier = classifier

    def evaluate(self, message: str) -> IntentDecision:
        """Classify ``message`` and decide whether execution may proceed."""
        classification = self._classifier.classify(message)
        allow_execution = not classification.requires_clarification
        routing_target = (
            self._route(classification.scope) if allow_execution else RoutingTarget.NONE
        )
        return IntentDecision(
            classification=classification,
            allow_execution=allow_execution,
            routing_target=routing_target,
        )

    @staticmethod
    def _route(scope: IntentScope) -> RoutingTarget:
        if scope is IntentScope.PERSONAL:
            return RoutingTarget.MEMORY
        if scope in (IntentScope.ORGANIZATIONAL, IntentScope.MIXED):
            return RoutingTarget.KNOWLEDGE
        return RoutingTarget.NONE

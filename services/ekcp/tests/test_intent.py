"""Tests for the deterministic intent classifier and gate."""

from __future__ import annotations

import pytest

from config.settings import IntentSettings
from domain.intent import (
    IntentClassifier,
    IntentError,
    IntentGate,
    IntentPolicy,
    IntentScope,
    IntentType,
    RoutingTarget,
)


def _gate(*, threshold: float = 0.6) -> IntentGate:
    policy = IntentPolicy.from_settings(
        IntentSettings(_env_file=None, confidence_threshold=threshold)
    )
    return IntentGate(IntentClassifier(policy))


def test_organizational_query_routes_to_knowledge() -> None:
    decision = _gate().evaluate("What is the company policy on remote work?")
    assert decision.classification.scope is IntentScope.ORGANIZATIONAL
    assert decision.allow_execution is True
    assert decision.routing_target is RoutingTarget.KNOWLEDGE


def test_personal_query_routes_to_memory() -> None:
    decision = _gate().evaluate("What did we discuss yesterday about my preferences?")
    assert decision.classification.scope is IntentScope.PERSONAL
    assert decision.routing_target is RoutingTarget.MEMORY


def test_task_intent_detected() -> None:
    decision = _gate().evaluate("Please generate the quarterly compliance report")
    assert decision.classification.intent is IntentType.TASK


def test_ambiguous_query_requests_clarification() -> None:
    decision = _gate().evaluate("hmm")
    assert decision.classification.requires_clarification is True
    assert decision.allow_execution is False
    assert decision.routing_target is RoutingTarget.NONE
    assert decision.classification.clarification_prompt
    assert decision.classification.suggested_interpretations


def test_empty_message_raises() -> None:
    with pytest.raises(IntentError):
        _gate().evaluate("   ")


def test_deterministic_classification() -> None:
    gate = _gate()
    first = gate.evaluate("What is the company documentation standard?")
    second = gate.evaluate("What is the company documentation standard?")
    assert first.classification == second.classification

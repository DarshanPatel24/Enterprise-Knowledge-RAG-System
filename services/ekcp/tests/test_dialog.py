"""Dialog context engine tests: turn classification, query rewriting, history.

Deterministic and hermetic (``_env_file=None``). Covers the four turn types, the
follow-up/clarification-reply query rewriting, token-budgeted history pruning,
fresh-question history drop, and the streaming clarification short-circuit.
"""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from api.app import create_app
from api.dependencies import build_resources, get_resources
from composition import build_dialog_engine
from config.settings import DialogSettings, EkcpSettings, IntentSettings
from domain.dialog import (
    CLARIFICATION_PROMPT,
    DialogContextEngine,
    DialogMessage,
    DialogPolicy,
    QuestionCondenser,
    TurnClassifier,
    TurnType,
)
from domain.intent import IntentClassifier, IntentPolicy

_CONTEXT = {
    "user_id": "analyst-1",
    "tenant_id": "tenant-a",
    "classification_clearance": "internal",
}


@pytest.fixture
def settings() -> EkcpSettings:
    return EkcpSettings(_env_file=None)


def _engine(**dialog_overrides: object) -> DialogContextEngine:
    dialog_settings = DialogSettings(_env_file=None, **dialog_overrides)  # type: ignore[arg-type]
    policy = DialogPolicy.from_settings(dialog_settings)
    intent = IntentClassifier(IntentPolicy.from_settings(IntentSettings(_env_file=None)))
    classifier = TurnClassifier(policy, intent)
    condenser = QuestionCondenser(
        enabled=False, provider="huggingface", model="", base_url="", temperature=0.0
    )
    return DialogContextEngine(policy, classifier, condenser=condenser)


def _client(settings: EkcpSettings) -> AsyncClient:
    app = create_app(settings)
    resources = build_resources(settings)
    app.dependency_overrides[get_resources] = lambda: resources
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://ekcp.test")


def test_fresh_question_drops_history() -> None:
    engine = _engine()
    history = [
        DialogMessage(role="user", content="how do I configure priority mapping in PSI"),
        DialogMessage(role="assistant", content="Open Configure then Priority Mapping."),
    ]
    decision = engine.decide("what is the DSAR purge workflow", history)
    assert decision.turn_type is TurnType.FRESH
    assert decision.search_query == "what is the DSAR purge workflow"
    assert decision.history == ()


def test_follow_up_anaphora_rewrites_query() -> None:
    engine = _engine()
    history = [
        DialogMessage(role="user", content="how do I configure priority mapping for PSI"),
        DialogMessage(role="assistant", content="Here are the configuration steps."),
    ]
    decision = engine.decide("what about the second one?", history)
    assert decision.turn_type is TurnType.FOLLOW_UP
    assert "priority mapping" in decision.search_query
    assert "second" in decision.search_query
    assert decision.history  # follow-ups carry prior turns for generation


def test_topic_continuation_is_follow_up() -> None:
    engine = _engine()
    history = [
        DialogMessage(role="user", content="explain priority mapping in PSI"),
        DialogMessage(role="assistant", content="Priority mapping standardizes alarms."),
    ]
    decision = engine.decide("how does priority mapping handle conflicts", history)
    assert decision.turn_type is TurnType.FOLLOW_UP
    assert "priority mapping" in decision.search_query


def test_vague_message_requests_clarification() -> None:
    engine = _engine()
    decision = engine.decide("help", [])
    assert decision.turn_type is TurnType.CLARIFICATION_NEEDED
    assert decision.clarification_prompt == CLARIFICATION_PROMPT
    assert decision.history == ()


def test_clarification_reply_links_original_question() -> None:
    engine = _engine()
    history = [
        DialogMessage(role="user", content="priority mapping"),
        DialogMessage(role="assistant", content=CLARIFICATION_PROMPT),
    ]
    decision = engine.decide("for PSI adhering to ISA 18.2", history)
    assert decision.turn_type is TurnType.CLARIFICATION_REPLY
    assert "priority mapping" in decision.search_query
    assert "PSI" in decision.search_query


def test_history_pruned_to_token_budget() -> None:
    engine = _engine(history_token_budget=70, chars_per_token=4)
    long_turn = "priority mapping configuration details " * 8
    history = [
        DialogMessage(role="user", content=long_turn + " first"),
        DialogMessage(role="assistant", content=long_turn + " second"),
        DialogMessage(role="user", content=long_turn + " third"),
        DialogMessage(role="assistant", content=long_turn + " latest"),
    ]
    decision = engine.decide("and what about conflicts", history)
    assert decision.turn_type is TurnType.FOLLOW_UP
    assert len(decision.history) == 1
    assert decision.history[-1].content.endswith("latest")


def test_clarification_can_be_disabled() -> None:
    engine = _engine(enable_clarification=False)
    decision = engine.decide("help", [])
    assert decision.turn_type is TurnType.FRESH
    assert decision.search_query == "help"


def test_build_dialog_engine_from_settings(settings: EkcpSettings) -> None:
    engine = build_dialog_engine(settings)
    decision = engine.decide("what is the remote work policy", [])
    assert decision.turn_type in (TurnType.FRESH, TurnType.CLARIFICATION_NEEDED)


async def test_chat_stream_clarifies_vague_message(settings: EkcpSettings) -> None:
    async with _client(settings) as client:
        response = await client.post(
            "/chat/stream",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"message": "help", "security_context": _CONTEXT},
        )
    assert response.status_code == httpx.codes.OK
    body = response.text
    assert "answer the right thing" in body
    assert "clarification" in body

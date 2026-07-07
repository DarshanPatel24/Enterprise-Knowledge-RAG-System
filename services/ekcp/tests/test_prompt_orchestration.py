"""Tests for prompt orchestration and citation-readiness validation."""

from __future__ import annotations

import pytest

from config.settings import PromptSettings
from contracts.retrieval import (
    Citation,
    RetrievalCandidate,
    RetrievalContextPackage,
)
from domain.context import (
    ContextItem,
    ContextSource,
    ExecutionContextPackage,
)
from domain.prompt import (
    PromptError,
    PromptOrchestrator,
    PromptPolicy,
    PromptTemplate,
    ValidationStatus,
    default_prompt_registry,
    validate_citation_readiness,
)


def _orchestrator(**overrides: object) -> PromptOrchestrator:
    settings = PromptSettings(_env_file=None, **overrides)  # type: ignore[arg-type]
    return PromptOrchestrator(
        PromptPolicy.from_settings(settings), registry=default_prompt_registry()
    )


def _ecp(*items: ContextItem) -> ExecutionContextPackage:
    return ExecutionContextPackage(
        context_id="ctx-1",
        tenant_id="tenant-a",
        conversation_id="conv-1",
        user_intent="What is the remote work policy?",
        items=tuple(items),
    )


def _enterprise_item() -> ContextItem:
    return ContextItem(
        source=ContextSource.ENTERPRISE,
        content="Remote work is allowed two days per week.",
        reason="evidence",
        rank_score=0.9,
        citation=Citation(document_id="d1", chunk_id="c1", source_path="/docs/hr.md"),
    )


def test_prompt_uses_named_variables_and_layers() -> None:
    package = _orchestrator().build(_ecp(_enterprise_item()))
    assert package.validation_status is ValidationStatus.VALID
    assert "What is the remote work policy?" in package.prompt_text
    assert "Remote work is allowed two days per week." in package.prompt_text
    assert "[cite: /docs/hr.md#c1]" in package.prompt_text
    assert package.template_id == "enterprise_chat_v1"
    assert package.token_estimate > 0


def test_prompt_renders_policies_layer() -> None:
    policy_item = ContextItem(
        source=ContextSource.POLICY,
        content="Never disclose salary data.",
        reason="policy",
        rank_score=1.0,
    )
    package = _orchestrator().build(_ecp(policy_item, _enterprise_item()))
    assert "Never disclose salary data." in package.prompt_text
    assert package.policy_context == ("Never disclose salary data.",)


def test_no_context_renders_placeholder() -> None:
    package = _orchestrator().build(_ecp())
    assert "No additional context available." in package.prompt_text


def test_unknown_template_raises() -> None:
    with pytest.raises(PromptError):
        _orchestrator().build(_ecp(), template_id="does-not-exist")


def test_token_exceeded_status() -> None:
    big = ContextItem(
        source=ContextSource.ENTERPRISE,
        content="word " * 2000,
        reason="evidence",
        rank_score=0.9,
        citation=Citation(document_id="d1", chunk_id="c1", source_path="/x.md"),
    )
    package = _orchestrator(max_prompt_tokens=10).build(_ecp(big))
    assert package.validation_status is ValidationStatus.TOKEN_EXCEEDED


def test_content_with_braces_is_safe() -> None:
    # Context content containing braces must not break variable substitution.
    item = ContextItem(
        source=ContextSource.ENTERPRISE,
        content="config is {not_a_var} in the file",
        reason="evidence",
        rank_score=0.9,
        citation=Citation(document_id="d1", chunk_id="c1", source_path="/x.md"),
    )
    package = _orchestrator().build(_ecp(item))
    assert "{not_a_var}" in package.prompt_text


def test_missing_variable_raises() -> None:
    # A template that declares a variable the orchestrator does not provide.
    broken = PromptTemplate(
        template_id="broken",
        layers=(),
        required_variables=("nonexistent_variable",),
    )
    orchestrator = PromptOrchestrator(
        PromptPolicy.from_settings(PromptSettings(_env_file=None)),
        registry={"broken": broken},
    )
    with pytest.raises(PromptError):
        orchestrator.build(_ecp(), template_id="broken")


def test_citation_readiness_strips_incomplete() -> None:
    package = RetrievalContextPackage(
        query="q",
        tenant_id="tenant-a",
        candidates=[
            RetrievalCandidate(
                citation=Citation(document_id="d1", chunk_id="c1", source_path="/a.md"),
                content="good",
                relevance_score=0.9,
            ),
            RetrievalCandidate(
                citation=Citation(document_id="d2", chunk_id="c2", source_path="/b.md"),
                content="   ",
                relevance_score=0.8,
            ),
        ],
    )
    ready, report = validate_citation_readiness(package)
    assert len(ready) == 1
    assert report.dropped == 1
    assert report.all_ready is False

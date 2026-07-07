"""Declarative prompt template registry.

Templates are enterprise assets defined as data (layered strings with explicit
``{variable}`` placeholders), never hardcoded prompt strings in engine logic. The
default registry ships a governed enterprise-chat template; additional templates
are registered here or loaded from a store in later sprints.
"""

from __future__ import annotations

from domain.prompt.models import PromptLayer, PromptLayerTemplate, PromptTemplate

DEFAULT_TEMPLATE_ID = "enterprise_chat_v1"

_ENTERPRISE_CHAT = PromptTemplate(
    template_id=DEFAULT_TEMPLATE_ID,
    version="1.0.0",
    layers=(
        PromptLayerTemplate(
            layer=PromptLayer.SYSTEM,
            template=(
                "You are {assistant_identity}. {assistant_behavior} "
                "Answer strictly from the provided context and cite sources. "
                "If the context is insufficient, say so."
            ),
        ),
        PromptLayerTemplate(
            layer=PromptLayer.POLICY,
            template="Organizational policies to honor:\n{organizational_policies}",
        ),
        PromptLayerTemplate(
            layer=PromptLayer.CONVERSATION,
            template="Conversation objective: {user_objective}",
        ),
        PromptLayerTemplate(
            layer=PromptLayer.TASK,
            template="Relevant context:\n{context_items}\n\nUser request: {user_objective}",
        ),
        PromptLayerTemplate(
            layer=PromptLayer.FORMATTING,
            template="Respond in {output_format} format.",
        ),
    ),
    required_variables=(
        "assistant_identity",
        "assistant_behavior",
        "organizational_policies",
        "user_objective",
        "context_items",
        "output_format",
    ),
)


def default_prompt_registry() -> dict[str, PromptTemplate]:
    """Return the default prompt template registry keyed by template id."""
    return {_ENTERPRISE_CHAT.template_id: _ENTERPRISE_CHAT}

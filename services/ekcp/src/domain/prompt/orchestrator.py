"""Prompt orchestrator: build a validated Prompt Package from context.

Constructs prompts by resolving explicit named variables into ordered
declarative template layers (system, policy, conversation, task, formatting).
No prompt strings are hardcoded here; templates come from the registry and
variables are injected from the Execution Context Package. Construction is
deterministic and validated (required variables present, token budget honored).
"""

from __future__ import annotations

import uuid

from domain.context.models import ContextSource, ExecutionContextPackage
from domain.context.tokens import estimate_tokens
from domain.observability import get_logger
from domain.prompt.errors import PromptError, PromptErrorType
from domain.prompt.models import (
    PromptPackage,
    PromptTemplate,
    ValidationStatus,
)
from domain.prompt.policy import PromptPolicy

logger = get_logger("ekcp.prompt.orchestrator")


class PromptOrchestrator:
    """Assemble validated prompt packages from templates and context."""

    def __init__(
        self, policy: PromptPolicy, *, registry: dict[str, PromptTemplate]
    ) -> None:
        self._policy = policy
        self._registry = registry

    def build(
        self,
        ecp: ExecutionContextPackage,
        *,
        template_id: str | None = None,
        output_format: str | None = None,
    ) -> PromptPackage:
        """Build a prompt package for ``ecp`` using the selected template."""
        selected_id = template_id or self._policy.default_template_id
        template = self._registry.get(selected_id)
        if template is None:
            raise PromptError(
                PromptErrorType.UNKNOWN_TEMPLATE, f"unknown template {selected_id!r}"
            )

        resolved_format = (
            output_format or template.output_format or self._policy.default_output_format
        )
        variables: dict[str, str] = {
            "assistant_identity": self._policy.assistant_identity,
            "assistant_behavior": self._policy.assistant_behavior,
            "user_objective": ecp.user_intent,
            "context_items": self._render_items(ecp),
            "organizational_policies": self._render_policies(ecp),
            "output_format": resolved_format,
        }

        missing = [name for name in template.required_variables if name not in variables]
        if missing:
            raise PromptError(
                PromptErrorType.MISSING_VARIABLE,
                f"missing required variables: {', '.join(sorted(missing))}",
            )

        rendered_layers: list[str] = []
        for layer in template.layers:
            try:
                text = layer.template.format_map(variables)
            except KeyError as exc:
                raise PromptError(
                    PromptErrorType.MISSING_VARIABLE,
                    f"template {selected_id!r} references undeclared variable {exc}",
                ) from exc
            if text.strip():
                rendered_layers.append(text.strip())

        prompt_text = "\n\n".join(rendered_layers)
        token_estimate = estimate_tokens(
            prompt_text, chars_per_token=self._policy.chars_per_token
        )
        status = (
            ValidationStatus.TOKEN_EXCEEDED
            if token_estimate > self._policy.max_prompt_tokens
            else ValidationStatus.VALID
        )
        policy_context = tuple(
            item.content for item in ecp.items if item.source is ContextSource.POLICY
        )

        logger.info(
            "prompt_generated",
            extra={
                "template_id": selected_id,
                "token_estimate": token_estimate,
                "validation_status": status,
            },
        )
        return PromptPackage(
            prompt_id=f"prm-{uuid.uuid4().hex[:12]}",
            prompt_text=prompt_text,
            template_id=template.template_id,
            template_version=template.version,
            context_id=ecp.context_id,
            variables_used=variables,
            policy_context=policy_context,
            token_estimate=token_estimate,
            compression_applied=ecp.compression_applied,
            validation_status=status,
        )

    @staticmethod
    def _render_items(ecp: ExecutionContextPackage) -> str:
        lines: list[str] = []
        for item in ecp.items:
            if item.source is ContextSource.POLICY:
                continue
            cite = ""
            if item.citation is not None:
                cite = f" [cite: {item.citation.source_path}#{item.citation.chunk_id}]"
            lines.append(f"- ({item.source}) {item.content}{cite}")
        return "\n".join(lines) if lines else "No additional context available."

    @staticmethod
    def _render_policies(ecp: ExecutionContextPackage) -> str:
        policies = [
            item.content for item in ecp.items if item.source is ContextSource.POLICY
        ]
        return "\n".join(f"- {p}" for p in policies) if policies else "None specified."

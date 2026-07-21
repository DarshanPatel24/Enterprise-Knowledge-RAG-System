"""Optional local-LLM question condenser (feature-flagged, off by default).

Rewrites a follow-up message into a standalone search query using the recent
conversation, via a LangChain LCEL chain over the configured local chat model.
Any failure -- missing dependency, unavailable model, or empty output -- degrades
gracefully to ``None`` so the deterministic rewrite path is always used as a
fallback and retrieval never breaks. All parameters come from settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from domain.dialog.history import render_history
from domain.integrations import build_chat_model
from domain.observability import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from domain.dialog.models import DialogMessage

logger = get_logger("ekcp.domain.dialog.condense")

_CONDENSE_SYSTEM_PROMPT = (
    "You rewrite a user's follow-up question into a single standalone search "
    "query using the conversation so far. Output ONLY the rewritten query with no "
    "preamble, quotes, or explanation. Preserve every product name, feature name, "
    "error code, and technical term. If the question is already standalone, return "
    "it unchanged."
)
_CONDENSE_HUMAN_TEMPLATE = (
    "Conversation so far:\n{history}\n\nFollow-up question: {question}\n\n"
    "Standalone search query:"
)


class QuestionCondenser:
    """LLM-backed follow-up condenser with a graceful deterministic fallback."""

    def __init__(
        self,
        *,
        enabled: bool,
        provider: str,
        model: str,
        base_url: str,
        temperature: float,
    ) -> None:
        self._enabled = enabled
        self._provider = provider
        self._model = model
        self._base_url = base_url
        self._temperature = temperature
        self._chain: Any = None

    @property
    def enabled(self) -> bool:
        """Return whether condensing is turned on and a model is configured."""
        return self._enabled and bool(self._model)

    def condense(self, message: str, history: Sequence[DialogMessage]) -> str | None:
        """Return a standalone query, or ``None`` to fall back to heuristics."""
        if not self.enabled:
            return None
        try:
            chain = self._ensure_chain()
            result = chain.invoke(
                {"history": render_history(history), "question": message.strip()}
            )
            text = str(result).strip()
            return text or None
        except Exception:  # noqa: BLE001 - degrade to heuristic; never fail retrieval
            logger.info("dialog_condense_degraded")
            return None

    def _ensure_chain(self) -> Any:  # noqa: ANN401 - LCEL chain type varies by provider
        if self._chain is None:
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.prompts import ChatPromptTemplate

            llm = build_chat_model(
                self._provider,
                self._model,
                base_url=self._base_url,
                temperature=self._temperature,
            )
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", _CONDENSE_SYSTEM_PROMPT),
                    ("human", _CONDENSE_HUMAN_TEMPLATE),
                ]
            )
            self._chain = prompt | llm | StrOutputParser()  # type: ignore[operator]
        return self._chain

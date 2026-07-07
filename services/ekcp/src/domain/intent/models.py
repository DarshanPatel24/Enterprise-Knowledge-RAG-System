"""Intent models for the intent-before-execution gate.

Intent classification is deterministic and explainable: it identifies the intent
type, the knowledge scope (personal versus organizational), a confidence score,
and the routing target. When confidence is insufficient the gate requests
clarification rather than executing on ambiguous input.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class IntentType(StrEnum):
    """High-level intent categories (flexible, not exhaustive)."""

    QUESTION = "question"
    TASK = "task"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"
    COLLABORATION = "collaboration"
    AGENT_REQUEST = "agent_request"


class IntentScope(StrEnum):
    """Knowledge scope that determines routing."""

    PERSONAL = "personal"
    ORGANIZATIONAL = "organizational"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class IntentComplexity(StrEnum):
    """Coarse complexity estimate used by downstream planning."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class RoutingTarget(StrEnum):
    """Where the resolved intent should source context from."""

    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    NONE = "none"


class IntentClassification(BaseModel):
    """Immutable classification of a single user message."""

    model_config = ConfigDict(frozen=True)

    intent: IntentType
    scope: IntentScope
    complexity: IntentComplexity
    confidence: float = Field(ge=0.0, le=1.0)
    requires_clarification: bool
    clarification_prompt: str = ""
    suggested_interpretations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class IntentDecision(BaseModel):
    """Immutable gate decision: whether execution may proceed and where to route."""

    model_config = ConfigDict(frozen=True)

    classification: IntentClassification
    allow_execution: bool
    routing_target: RoutingTarget

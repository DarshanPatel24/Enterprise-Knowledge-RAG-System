"""Structured Query Model: the immutable, versioned query intelligence output.

Each engine in the Query Intelligence Domain produces a new immutable model
rather than mutating a previous stage. The aggregate :class:`StructuredQuery`
records every transformation so execution decisions are fully explainable.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RetrievalIntent(StrEnum):
    """Enterprise retrieval intents (handbook Chapter 10)."""

    EXACT_LOOKUP = "exact_lookup"
    NAVIGATION = "navigation"
    RESEARCH = "research"
    COMPARISON = "comparison"
    DISCOVERY = "discovery"
    COMPLIANCE = "compliance"
    ANALYTICAL = "analytical"
    AI_CONTEXT = "ai_context"


class QueryComplexity(StrEnum):
    """Estimated retrieval complexity of a query."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class RetrievalProfile(StrEnum):
    """Retrieval configuration profiles (handbook Chapter 8.5)."""

    PRECISION = "precision"
    RECALL = "recall"
    BALANCED = "balanced"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"


class RetrievalEngineType(StrEnum):
    """Retrieval engines the planner may select (handbook Chapter 13.10)."""

    VECTOR = "vector"
    KEYWORD = "keyword"
    METADATA = "metadata"


class RankingStrategy(StrEnum):
    """Ranking strategies the planner may configure."""

    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    METADATA_WEIGHTED = "metadata_weighted"


class MetadataFilter(BaseModel):
    """A structured metadata constraint extracted from the query."""

    model_config = ConfigDict(frozen=True)

    field: str = Field(min_length=1)
    operator: str = "eq"
    value: str = Field(min_length=1)


class QueryUnderstanding(BaseModel):
    """Structured Query Model v1 produced by the Query Understanding Engine."""

    model_config = ConfigDict(frozen=True)

    query_id: str = Field(min_length=1)
    original_query: str
    normalized_query: str
    detected_language: str
    entities: tuple[str, ...] = ()
    metadata_filters: tuple[MetadataFilter, ...] = ()
    enterprise_terms: tuple[str, ...] = ()
    dates: tuple[str, ...] = ()
    numbers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "deterministic"


class IntentClassification(BaseModel):
    """Retrieval Query Model produced by the Intent Classification Engine."""

    model_config = ConfigDict(frozen=True)

    intent: RetrievalIntent
    confidence: float = Field(ge=0.0, le=1.0)
    complexity: QueryComplexity
    expected_recall: float = Field(ge=0.0, le=1.0)
    expected_precision: float = Field(ge=0.0, le=1.0)
    suggested_profile: RetrievalProfile
    suggested_candidate_count: int = Field(gt=0)
    secondary_intents: tuple[RetrievalIntent, ...] = ()
    warnings: tuple[str, ...] = ()


class TermExpansion(BaseModel):
    """A single term mapped to its enrichment expansions."""

    model_config = ConfigDict(frozen=True)

    term: str = Field(min_length=1)
    expansions: tuple[str, ...] = ()


class QueryEnrichment(BaseModel):
    """Enrichment output: synonym, ontology, and business-term expansions."""

    model_config = ConfigDict(frozen=True)

    expansions: tuple[TermExpansion, ...] = ()
    enriched_terms: tuple[str, ...] = ()


class RetrievalStep(BaseModel):
    """A single retrieval engine invocation within the execution plan."""

    model_config = ConfigDict(frozen=True)

    engine: RetrievalEngineType
    candidate_limit: int = Field(gt=0)
    timeout_ms: float = Field(gt=0.0)
    parallel_group: int = Field(ge=0)


class RetrievalPlan(BaseModel):
    """Retrieval Execution Plan produced by the Query Planner (handbook 13.5)."""

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(min_length=1)
    profile: RetrievalProfile
    steps: tuple[RetrievalStep, ...]
    ranking_strategy: RankingStrategy
    total_candidate_limit: int = Field(gt=0)
    total_timeout_ms: float = Field(gt=0.0)


class Transformation(BaseModel):
    """An explainability record of one transformation applied to the query."""

    model_config = ConfigDict(frozen=True)

    stage: str = Field(min_length=1)
    description: str


class StructuredQuery(BaseModel):
    """The aggregate, immutable query intelligence result for one request."""

    model_config = ConfigDict(frozen=True)

    query_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    understanding: QueryUnderstanding
    intent: IntentClassification
    enrichment: QueryEnrichment
    plan: RetrievalPlan
    transformations: tuple[Transformation, ...] = ()

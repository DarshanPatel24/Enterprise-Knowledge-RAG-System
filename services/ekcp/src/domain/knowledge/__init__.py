"""Knowledge integration domain (handbook Chapter 16)."""

from domain.knowledge.circuit_breaker import CircuitBreaker, CircuitState
from domain.knowledge.client import EkreHttpKnowledgeClient, KnowledgeClient
from domain.knowledge.errors import KnowledgeError, KnowledgeErrorType
from domain.knowledge.models import KnowledgeResult
from domain.knowledge.policy import KnowledgePolicy, KnowledgeSettingsLike
from domain.knowledge.retriever import KnowledgeRetriever

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "EkreHttpKnowledgeClient",
    "KnowledgeClient",
    "KnowledgeError",
    "KnowledgeErrorType",
    "KnowledgePolicy",
    "KnowledgeResult",
    "KnowledgeRetriever",
    "KnowledgeSettingsLike",
]

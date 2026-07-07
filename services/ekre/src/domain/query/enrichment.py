"""Query Enrichment Engine (handbook Chapter 11).

Expands the understood query with synonyms, business vocabulary, and enterprise
terminology so downstream retrieval covers equivalent phrasings. Expansion is
deterministic and driven by the injected :class:`EnterpriseVocabulary`.
"""

from __future__ import annotations

from domain.query.models import QueryEnrichment, QueryUnderstanding, TermExpansion
from domain.query.policy import EnterpriseVocabulary


class QueryEnrichmentEngine:
    """Deterministic synonym and business-vocabulary expansion engine."""

    def __init__(self, *, vocabulary: EnterpriseVocabulary) -> None:
        self._vocabulary = vocabulary

    def enrich(self, understanding: QueryUnderstanding) -> QueryEnrichment:
        """Produce synonym and terminology expansions for the query."""
        synonyms = self._vocabulary.synonyms
        expansions: list[TermExpansion] = []
        enriched: list[str] = []

        for token in self._candidate_terms(understanding):
            mapped = synonyms.get(token)
            if mapped:
                expansions.append(TermExpansion(term=token, expansions=tuple(mapped)))
                enriched.extend(mapped)

        # Enterprise acronym expansions resolved during understanding also enrich.
        enriched.extend(understanding.enterprise_terms)

        return QueryEnrichment(
            expansions=tuple(expansions),
            enriched_terms=tuple(dict.fromkeys(enriched)),
        )

    def _candidate_terms(self, understanding: QueryUnderstanding) -> tuple[str, ...]:
        tokens = understanding.normalized_query.lower().split()
        return tuple(dict.fromkeys(tokens))

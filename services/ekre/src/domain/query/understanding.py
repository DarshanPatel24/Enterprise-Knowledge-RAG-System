"""Query Understanding Engine (handbook Chapter 9).

Transforms a raw user query into a clean, normalized Structured Query Model v1.
The engine performs linguistic and structural preprocessing only; it determines
no retrieval intent and selects no strategy. All processing is deterministic.
"""

from __future__ import annotations

import re
import unicodedata

from domain.query.errors import QueryIntelligenceError, QueryIntelligenceErrorType
from domain.query.models import MetadataFilter, QueryUnderstanding
from domain.query.policy import EnterpriseVocabulary, QueryPolicy

# Structural extraction patterns (deterministic).
_WHITESPACE = re.compile(r"\s+")
_QUOTED = re.compile(r"\"([^\"]+)\"")
_METADATA_FILTER = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*):([^\s]+)")
_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{4})\b")
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_ACRONYM_TOKEN = re.compile(r"\b[A-Z]{2,}\b")
_CAPITALIZED = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)\b")

# Metadata operator aliases so `after:2024` reads as a range constraint.
_OPERATOR_KEYS = {"after": "gte", "before": "lte", "since": "gte", "until": "lte"}
# Metadata field aliases: `product:` targets the source_group tag EKIE derives
# from the document folder, so users filter by product without knowing the field.
_FIELD_ALIASES = {"product": "source_group"}
# Fields whose values are case-insensitive slugs and are normalized to lowercase.
_GROUP_FIELDS = frozenset({"source_group"})
# Non-ASCII-heavy queries keep the configured default language; deterministic.
_NON_ASCII = re.compile(r"[^\x00-\x7f]")


class QueryUnderstandingEngine:
    """Deterministic linguistic and structural preprocessing engine."""

    def __init__(self, policy: QueryPolicy, *, vocabulary: EnterpriseVocabulary) -> None:
        self._policy = policy
        self._vocabulary = vocabulary

    def run(
        self,
        raw_query: str,
        *,
        query_id: str,
        language: str | None = None,
    ) -> QueryUnderstanding:
        """Produce the Structured Query Model v1 for ``raw_query``."""
        stripped = raw_query.strip()
        if not stripped:
            raise QueryIntelligenceError(
                QueryIntelligenceErrorType.EMPTY_QUERY, "query must not be empty"
            )
        if len(stripped) > self._policy.max_query_length:
            raise QueryIntelligenceError(
                QueryIntelligenceErrorType.QUERY_TOO_LONG,
                f"query exceeds the maximum length of {self._policy.max_query_length}",
            )

        warnings: list[str] = []
        metadata_filters = self._extract_metadata_filters(stripped)
        entities = self._extract_entities(stripped)
        dates = tuple(dict.fromkeys(_DATE.findall(stripped)))
        normalized = self._normalize(stripped)
        numbers = tuple(dict.fromkeys(_NUMBER.findall(normalized)))
        enterprise_terms = self._resolve_enterprise_terms(normalized)
        detected_language = self._detect_language(normalized, language)

        if not entities and not metadata_filters:
            warnings.append("no entities or metadata constraints detected")

        confidence = self._confidence(stripped, normalized, entities, enterprise_terms)

        return QueryUnderstanding(
            query_id=query_id,
            original_query=raw_query,
            normalized_query=normalized,
            detected_language=detected_language,
            entities=entities,
            metadata_filters=metadata_filters,
            enterprise_terms=enterprise_terms,
            dates=dates,
            numbers=numbers,
            warnings=tuple(warnings),
            confidence=confidence,
            source="deterministic",
        )

    def _normalize(self, query: str) -> str:
        normalized = unicodedata.normalize("NFKC", query)
        normalized = normalized.replace("\u201c", '"').replace("\u201d", '"')
        normalized = normalized.replace("\u2018", "'").replace("\u2019", "'")
        # Drop metadata-filter tokens from the free-text query; they are structured.
        normalized = _METADATA_FILTER.sub(" ", normalized)
        normalized = _WHITESPACE.sub(" ", normalized).strip()
        return normalized

    def _extract_metadata_filters(self, query: str) -> tuple[MetadataFilter, ...]:
        filters: list[MetadataFilter] = []
        seen_fields: set[str] = set()
        for raw_field, value in _METADATA_FILTER.findall(query):
            field = _FIELD_ALIASES.get(raw_field.lower(), raw_field.lower())
            operator = _OPERATOR_KEYS.get(raw_field.lower(), "eq")
            resolved = value.strip().lower() if field in _GROUP_FIELDS else value
            filters.append(MetadataFilter(field=field, operator=operator, value=resolved))
            seen_fields.add(field)
        product_group = self._detect_product_group(query)
        if product_group and "source_group" not in seen_fields:
            filters.append(
                MetadataFilter(field="source_group", operator="eq", value=product_group)
            )
        return tuple(filters)

    def _detect_product_group(self, query: str) -> str | None:
        """Return the source_group for a known product phrase in the query, if any."""
        products = self._vocabulary.products
        if not products:
            return None
        lowered = query.lower()
        # Longest phrase first for the most specific match; deterministic tie-break.
        for phrase in sorted(products, key=lambda item: (-len(item), item)):
            if phrase and phrase in lowered:
                return products[phrase]
        return None

    def _extract_entities(self, query: str) -> tuple[str, ...]:
        quoted = [match.strip() for match in _QUOTED.findall(query) if match.strip()]
        # Ignore metadata-filter fragments when scanning for capitalized entities.
        without_filters = _METADATA_FILTER.sub(" ", query)
        capitalized = [m.strip() for m in _CAPITALIZED.findall(without_filters) if m.strip()]
        return tuple(dict.fromkeys([*quoted, *capitalized]))

    def _resolve_enterprise_terms(self, normalized: str) -> tuple[str, ...]:
        terms: list[str] = []
        acronyms = self._vocabulary.acronyms
        for token in _ACRONYM_TOKEN.findall(normalized):
            expansion = acronyms.get(token.lower())
            if expansion:
                terms.append(expansion)
        for token in normalized.lower().split():
            expansion = acronyms.get(token)
            if expansion and expansion not in terms:
                terms.append(expansion)
        return tuple(dict.fromkeys(terms))

    def _detect_language(self, normalized: str, language: str | None) -> str:
        if language:
            return language
        # Deterministic heuristic: non-ASCII-heavy text keeps the configured
        # default rather than guessing a specific language offline.
        return self._policy.default_language

    def _confidence(
        self,
        original: str,
        normalized: str,
        entities: tuple[str, ...],
        enterprise_terms: tuple[str, ...],
    ) -> float:
        confidence = 0.6
        if entities:
            confidence += 0.2
        if enterprise_terms:
            confidence += 0.1
        if _NON_ASCII.search(original):
            confidence -= 0.1
        return max(0.0, min(1.0, round(confidence, 3)))

"""EKRE knowledge client: the boundary to the retrieval engine (handbook 16).

The client posts a query plus the propagated security context to EKRE's
``/v1/query/retrieve`` endpoint and returns the citation-preserving
``RetrievalContextPackage``. The HTTP dependency is imported lazily so the
offline path never requires ``httpx``; a 429 is surfaced as backpressure and a
timeout as a controlled failure so the retriever can degrade gracefully.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from contracts.retrieval import RetrievalContextPackage
from domain.knowledge.errors import KnowledgeError, KnowledgeErrorType


class KnowledgeClient(ABC):
    """Abstract client for retrieving enterprise knowledge from EKRE."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str,
        security_context: dict[str, str],
        correlation_id: str | None = None,
    ) -> RetrievalContextPackage:
        """Retrieve knowledge for ``query`` or raise :class:`KnowledgeError`."""


class EkreHttpKnowledgeClient(KnowledgeClient):
    """HTTP client that calls the EKRE ``/v1/query/retrieve`` endpoint."""

    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str,
        security_context: dict[str, str],
        correlation_id: str | None = None,
    ) -> RetrievalContextPackage:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - httpx present in this repo
            raise KnowledgeError(
                KnowledgeErrorType.EKRE_UNAVAILABLE,
                "httpx is required to call EKRE; install it to enable knowledge",
            ) from exc

        headers = {"X-Tenant-ID": tenant_id}
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        payload = {"query": query, "security_context": security_context}
        try:
            response = httpx.post(
                f"{self._base_url}/v1/query/retrieve",
                json=payload,
                headers=headers,
                timeout=self._timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise KnowledgeError(
                KnowledgeErrorType.TIMEOUT, "EKRE retrieval timed out"
            ) from exc
        except httpx.HTTPError as exc:
            raise KnowledgeError(
                KnowledgeErrorType.EKRE_UNAVAILABLE, f"EKRE request failed: {exc}"
            ) from exc

        if response.status_code == 429:
            raise KnowledgeError(
                KnowledgeErrorType.BACKPRESSURE, "EKRE is applying backpressure (429)"
            )
        if response.status_code != 200:
            raise KnowledgeError(
                KnowledgeErrorType.RETRIEVAL_FAILED,
                f"EKRE returned status {response.status_code}",
            )
        body = response.json()
        package_data = body.get("package", body)
        return RetrievalContextPackage.model_validate(package_data)

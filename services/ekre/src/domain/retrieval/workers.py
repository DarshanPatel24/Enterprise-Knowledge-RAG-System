"""Concrete retrieval workers (handbook Chapters 19-21).

Each worker implements the execution-domain :class:`RetrievalWorker` contract,
executes exactly one retrieval mode against a repository connector, applies the
pre-pool security filter, and returns standardized candidates. Workers make no
planning, ranking, or fusion decisions.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from contracts.retrieval import RetrievalCandidate
from contracts.security_context import SecurityContext
from domain.connectors.base import RepositoryConnector
from domain.execution.models import RetrievalTask, WorkerDescriptor
from domain.execution.worker import RetrievalWorker
from domain.query.models import RetrievalEngineType
from domain.retrieval.embedding import EmbeddingAdapter
from domain.retrieval.normalize import to_candidates
from domain.retrieval.security import (
    enforce_clearance,
    enforce_tenant,
    resolve_allowed_clearances,
)

_TOKEN = re.compile(r"[A-Za-z0-9_\-]+")


class VectorRetrievalWorker(RetrievalWorker):
    """Executes semantic search using the inherited embedding model."""

    def __init__(
        self,
        connector: RepositoryConnector,
        adapter: EmbeddingAdapter,
        *,
        collection: str,
        require_security_context: bool = True,
        require_tenant_scope: bool = True,
        worker_id: str = "vector-worker",
    ) -> None:
        self._connector = connector
        self._adapter = adapter
        self._collection = collection
        self._require = require_security_context
        self._require_tenant = require_tenant_scope
        self._descriptor = WorkerDescriptor(
            worker_id=worker_id,
            engine=RetrievalEngineType.VECTOR,
            supported_task_types=(RetrievalEngineType.VECTOR.value,),
        )

    @property
    def descriptor(self) -> WorkerDescriptor:
        """Return the worker's capability advertisement."""
        return self._descriptor

    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        """Embed the query and execute a clearance- and tenant-filtered vector search."""
        allowed = resolve_allowed_clearances(
            security_context, require_security_context=self._require
        )
        tenant_id = task.tenant_id if self._require_tenant else ""
        vector = self._adapter.embed(task.query)
        documents = self._connector.vector_search(
            self._collection,
            vector,
            limit=task.candidate_limit,
            allowed_clearances=allowed,
            tenant_id=tenant_id,
            metadata_filters=task.metadata_filters,
        )
        documents = enforce_clearance(documents, allowed)
        documents = enforce_tenant(documents, tenant_id)
        return to_candidates(documents, explanation="vector similarity")


class KeywordRetrievalWorker(RetrievalWorker):
    """Executes lexical exact-term search."""

    def __init__(
        self,
        connector: RepositoryConnector,
        *,
        collection: str,
        require_security_context: bool = True,
        require_tenant_scope: bool = True,
        worker_id: str = "keyword-worker",
    ) -> None:
        self._connector = connector
        self._collection = collection
        self._require = require_security_context
        self._require_tenant = require_tenant_scope
        self._descriptor = WorkerDescriptor(
            worker_id=worker_id,
            engine=RetrievalEngineType.KEYWORD,
            supported_task_types=(RetrievalEngineType.KEYWORD.value,),
        )

    @property
    def descriptor(self) -> WorkerDescriptor:
        """Return the worker's capability advertisement."""
        return self._descriptor

    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        """Tokenize the query and execute a clearance- and tenant-filtered keyword search."""
        allowed = resolve_allowed_clearances(
            security_context, require_security_context=self._require
        )
        tenant_id = task.tenant_id if self._require_tenant else ""
        terms = _TOKEN.findall(task.query)
        documents = self._connector.keyword_search(
            self._collection,
            terms,
            limit=task.candidate_limit,
            allowed_clearances=allowed,
            tenant_id=tenant_id,
            metadata_filters=task.metadata_filters,
        )
        documents = enforce_clearance(documents, allowed)
        documents = enforce_tenant(documents, tenant_id)
        return to_candidates(documents, explanation="keyword match")


class MetadataRetrievalWorker(RetrievalWorker):
    """Executes structured metadata attribute search."""

    def __init__(
        self,
        connector: RepositoryConnector,
        *,
        collection: str,
        require_security_context: bool = True,
        require_tenant_scope: bool = True,
        worker_id: str = "metadata-worker",
    ) -> None:
        self._connector = connector
        self._collection = collection
        self._require = require_security_context
        self._require_tenant = require_tenant_scope
        self._descriptor = WorkerDescriptor(
            worker_id=worker_id,
            engine=RetrievalEngineType.METADATA,
            supported_task_types=(RetrievalEngineType.METADATA.value,),
        )

    @property
    def descriptor(self) -> WorkerDescriptor:
        """Return the worker's capability advertisement."""
        return self._descriptor

    def retrieve(
        self, task: RetrievalTask, *, security_context: SecurityContext | None
    ) -> Sequence[RetrievalCandidate]:
        """Execute a clearance- and tenant-filtered metadata search over the task filters."""
        allowed = resolve_allowed_clearances(
            security_context, require_security_context=self._require
        )
        tenant_id = task.tenant_id if self._require_tenant else ""
        documents = self._connector.metadata_search(
            self._collection,
            task.metadata_filters,
            limit=task.candidate_limit,
            allowed_clearances=allowed,
            tenant_id=tenant_id,
        )
        documents = enforce_clearance(documents, allowed)
        documents = enforce_tenant(documents, tenant_id)
        return to_candidates(documents, explanation="metadata match")

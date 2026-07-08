"""Workflow persistence (in-memory offline default)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.workflow.errors import WorkflowError, WorkflowErrorType
from domain.workflow.models import Workflow


class WorkflowStore(ABC):
    """Abstract workflow persistence keyed by tenant and workflow id."""

    @abstractmethod
    def get(self, tenant_id: str, workflow_id: str) -> Workflow:
        """Return the stored workflow, or raise ``NOT_FOUND``."""

    @abstractmethod
    def save(self, workflow: Workflow) -> None:
        """Persist (insert or replace) a workflow."""


class InMemoryWorkflowStore(WorkflowStore):
    """Deterministic in-memory workflow store (local-first default)."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Workflow] = {}

    def get(self, tenant_id: str, workflow_id: str) -> Workflow:
        workflow = self._items.get((tenant_id, workflow_id))
        if workflow is None:
            raise WorkflowError(
                WorkflowErrorType.NOT_FOUND,
                f"workflow {workflow_id} not found for tenant {tenant_id}",
            )
        return workflow

    def save(self, workflow: Workflow) -> None:
        self._items[(workflow.tenant_id, workflow.workflow_id)] = workflow

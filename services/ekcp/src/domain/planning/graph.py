"""Dependency graph utilities: deterministic topological order and cycle detection."""

from __future__ import annotations

from collections.abc import Sequence

from domain.planning.errors import PlanningError, PlanningErrorType
from domain.planning.models import Task


def topological_order(tasks: Sequence[Task]) -> list[Task]:
    """Return tasks in dependency order, raising ``CYCLE_DETECTED`` on a cycle.

    Ties are broken by (priority, task_id) so the ordering is deterministic.
    """
    by_id = {task.task_id: task for task in tasks}
    indegree = {task.task_id: 0 for task in tasks}
    dependents: dict[str, list[str]] = {task.task_id: [] for task in tasks}
    for task in tasks:
        for dependency in task.dependencies:
            if dependency not in by_id:
                continue
            indegree[task.task_id] += 1
            dependents[dependency].append(task.task_id)

    ready = sorted(
        (tid for tid, degree in indegree.items() if degree == 0),
        key=lambda tid: (by_id[tid].priority, tid),
    )
    ordered: list[Task] = []
    while ready:
        current = ready.pop(0)
        ordered.append(by_id[current])
        for dependent in dependents[current]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
        ready.sort(key=lambda tid: (by_id[tid].priority, tid))

    if len(ordered) != len(tasks):
        raise PlanningError(
            PlanningErrorType.CYCLE_DETECTED,
            "task dependency graph contains a cycle",
        )
    return ordered

"""Rules over a list of tasks: the next ID, lookup by ID, and the order to show."""

from collections.abc import Sequence
from datetime import datetime

from task_tracker.domain.priority import Priority
from task_tracker.domain.status import Status
from task_tracker.domain.task import Task

# Highest priority first. The rank is the enum's definition order, because the
# string values sort CRITICAL, HIGH, LOW, MEDIUM (Review Focus 1).
_PRIORITY_RANK = {priority: rank for rank, priority in enumerate(Priority)}


def next_id(tasks: Sequence[Task]) -> int:
    """Return the ID for a new task: the highest ID plus one (D5).

    Not a count, so a gap left by a delete is not reused.
    """
    return max((task.id for task in tasks), default=0) + 1


def find(tasks: Sequence[Task], task_id: int) -> Task:
    """Return the task with `task_id`, or raise `ValueError` if there is none."""
    for task in tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"no task with ID {task_id}")


def _current_order(task: Task) -> tuple[datetime, int, int]:
    """Sort key for the current tasks: due date, priority, then ID.

    `datetime.max` stands in for a missing due date, so those tasks sort after
    every task that has one (Q2). A stored date has whole seconds, so it can never
    equal it. The ID settles ties, so the order does not depend on how the file
    was written.
    """
    # D6 chose naive local time on purpose, so DTZ901 does not apply to `max`.
    return (
        task.due or datetime.max,  # noqa: DTZ901
        _PRIORITY_RANK[task.priority],
        task.id,
    )


def _done_order(task: Task) -> tuple[datetime, int]:
    """Sort key for the done tasks: date completed, then ID (M4)."""
    # `Task` and `load` already refuse a DONE task without a date completed. This
    # says so again in every mode (`python -O` removes an assert), and tells pyright.
    if task.date_completed is None:
        raise ValueError(f"task {task.id} is DONE but has no date completed")
    return (task.date_completed, task.id)


def current_tasks(tasks: Sequence[Task]) -> list[Task]:
    """Return the tasks that are not done, in the order `list` shows them (M3)."""
    current = (task for task in tasks if task.status is not Status.DONE)
    return sorted(current, key=_current_order)


def done_tasks(tasks: Sequence[Task]) -> list[Task]:
    """Return the done tasks, by date completed and then ID (M4).

    Raises `ValueError` for a done task that has no date completed.
    """
    done = (task for task in tasks if task.status is Status.DONE)
    return sorted(done, key=_done_order)

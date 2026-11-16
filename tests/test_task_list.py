"""Tests for the rules over a list of tasks: the next ID, lookup, and the order."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

from datetime import datetime

import pytest

from task_tracker.domain.priority import Priority
from task_tracker.domain.status import Status
from task_tracker.domain.task import Task
from task_tracker.domain.task_list import current_tasks, done_tasks, find, next_id

# D6 chose naive local time on purpose, so DTZ001 does not apply to these values.
NOV_1 = datetime(2026, 11, 1)  # noqa: DTZ001
NOV_2 = datetime(2026, 11, 2)  # noqa: DTZ001
OCT_5 = datetime(2026, 10, 5)  # noqa: DTZ001
OCT_10 = datetime(2026, 10, 10)  # noqa: DTZ001


def _done(task_id: int, completed: datetime) -> Task:
    # The ordering reads only the status and the date completed, and a past date
    # completed passes the timeline rules only through `Task.restore`.
    task = Task(task_id, f"done {task_id}")
    task.status = Status.DONE
    task.date_completed = completed
    return task


def _names(tasks: list[Task]) -> list[str]:
    return [task.name for task in tasks]


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ([], 1),
        ([1, 5], 6),
        ([1, 2], 3),
        ([1, 3], 4),
    ],
    ids=["empty-list", "highest-plus-one-not-a-count", "highest-id-freed", "gap-kept"],
)
def test_next_id_is_the_highest_id_plus_one(stored: list[int], expected: int):
    # [1, 5]: a count would give 3. [1, 2] is 1 to 3 after deleting 3, so the 3
    # comes back. [1, 3] is 1 to 3 after deleting 2, and the gap is not filled (D5).
    tasks = [Task(task_id, "task") for task_id in stored]

    assert next_id(tasks) == expected


def test_find_returns_the_task_with_that_id():
    wanted = Task(2, "second")

    assert find([Task(1, "first"), wanted, Task(3, "third")], 2) is wanted


def test_find_raises_for_an_id_that_is_not_stored():
    with pytest.raises(ValueError, match="no task with ID 9"):
        find([Task(1, "first")], 9)


def test_current_tasks_leave_out_the_done_ones():
    tasks = [Task(1, "open"), _done(2, OCT_5)]

    assert _names(current_tasks(tasks)) == ["open"]


def test_current_tasks_put_the_earliest_due_date_first_and_no_due_date_last():
    tasks = [
        Task(1, "none"),
        Task(2, "later", due=NOV_2),
        Task(3, "sooner", due=NOV_1),
    ]

    assert _names(current_tasks(tasks)) == ["sooner", "later", "none"]


def test_current_tasks_break_a_due_date_tie_by_priority_not_by_label_order():
    # The labels sort CRITICAL, HIGH, LOW, MEDIUM, so a sort on the text would put
    # LOW before MEDIUM. The rank is the order the enum is defined in.
    tasks = [
        Task(1, "a-low", priority=Priority.LOW),
        Task(2, "b-critical", priority=Priority.CRITICAL),
        Task(3, "c-medium", priority=Priority.MEDIUM),
        Task(4, "d-high", priority=Priority.HIGH),
    ]

    assert _names(current_tasks(tasks)) == ["b-critical", "d-high", "c-medium", "a-low"]


def test_current_tasks_break_a_full_tie_by_id_whatever_the_stored_order():
    tasks = [Task(3, "third"), Task(1, "first"), Task(2, "second")]

    assert _names(current_tasks(tasks)) == ["first", "second", "third"]


def test_done_tasks_leave_out_the_current_ones():
    tasks = [Task(1, "open"), _done(2, OCT_5)]

    assert _names(done_tasks(tasks)) == ["done 2"]


def test_done_tasks_come_by_date_completed_and_then_id():
    # By ID alone this would be 1, 2, 3.
    tasks = [_done(1, OCT_10), _done(3, OCT_5), _done(2, OCT_5)]

    assert [task.id for task in done_tasks(tasks)] == [2, 3, 1]


def test_done_tasks_raise_for_a_done_task_without_a_date_completed():
    ghost = Task(5, "ghost")
    ghost.status = Status.DONE

    with pytest.raises(ValueError, match="task 5 is DONE but has no date completed"):
        done_tasks([ghost])

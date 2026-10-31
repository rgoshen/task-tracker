"""Tests for the Task record."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

from datetime import datetime

import pytest

from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.task import Task

TIMESTAMP_FIELDS = ["created", "updated", "start", "stop"]


def test_new_task_has_the_documented_defaults():
    task = Task(id=1, name="Buy milk")

    assert task.status is Status.TO_DO
    assert task.priority is Priority.LOW
    assert task.description == ""
    assert task.due is None
    assert task.date_completed is None


@pytest.mark.parametrize("field_name", TIMESTAMP_FIELDS)
def test_timestamp_defaults_to_the_moment_the_task_is_created(field_name: str):
    # D6 chose naive local time on purpose, so DTZ005 does not apply here.
    before = datetime.now()  # noqa: DTZ005
    task = Task(id=1, name="Buy milk")
    after = datetime.now()  # noqa: DTZ005

    assert before <= getattr(task, field_name) <= after


@pytest.mark.parametrize("field_name", TIMESTAMP_FIELDS)
def test_default_timestamps_are_naive_local_time(field_name: str):
    task = Task(id=1, name="Buy milk")

    assert getattr(task, field_name).tzinfo is None


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected(name: str):
    with pytest.raises(ValueError, match="name"):
        Task(id=1, name=name)


def test_non_string_name_is_rejected_with_value_error():
    # A hand-edited tasks.json can hold null, and the loader must see ValueError.
    with pytest.raises(ValueError, match="name"):
        Task(id=1, name=None)  # type: ignore[arg-type]


def test_name_is_stored_without_surrounding_whitespace():
    assert Task(id=1, name="  Buy milk  ").name == "Buy milk"


def test_status_and_priority_labels_become_enum_members():
    task = Task(id=1, name="x", status="DONE", priority="HIGH")  # type: ignore[arg-type]

    assert task.status is Status.DONE
    assert task.priority is Priority.HIGH


@pytest.mark.parametrize(
    ("field_name", "label"), [("status", "FINISHED"), ("priority", "URGENT")]
)
def test_unknown_status_or_priority_label_is_rejected(field_name: str, label: str):
    with pytest.raises(ValueError, match=label):
        Task(**{"id": 1, "name": "x", field_name: label})  # type: ignore[arg-type]

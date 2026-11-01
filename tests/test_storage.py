"""Tests for saving tasks to a JSON file and loading them back."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

import json
from datetime import datetime
from pathlib import Path

import pytest

from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.storage import load, save
from task_tracker.task import Task

# D6 chose naive local time on purpose, so DTZ001 does not apply to these values.
DUE = datetime(2026, 11, 1, 9, 0, 0)  # noqa: DTZ001
OPENED = datetime(2026, 10, 10, 9, 0, 0)  # noqa: DTZ001
FILED = datetime(2026, 10, 15, 17, 30, 0)  # noqa: DTZ001
RECORD_FIELDS = {
    "id",
    "name",
    "description",
    "created",
    "updated",
    "due",
    "date_completed",
    "status",
    "priority",
    "start",
    "stop",
}


@pytest.fixture(name="two_tasks")
def _two_tasks() -> list[Task]:
    buy_milk = Task(1, "Buy milk", priority=Priority.HIGH, due=DUE)
    # Done in the past, which only `restore` can build.
    file_taxes = Task.restore(
        2,
        "File taxes",
        description="",
        created=OPENED,
        updated=FILED,
        due=None,
        date_completed=FILED,
        status=Status.DONE,
        priority=Priority.LOW,
        start=OPENED,
        stop=FILED,
    )
    return [buy_milk, file_taxes]


def test_loading_a_missing_file_gives_an_empty_list_and_creates_nothing(
    tmp_path: Path,
):
    assert load(tmp_path / "tasks.json") == []
    assert not any(tmp_path.iterdir())


def test_loading_from_a_missing_directory_does_not_create_it(tmp_path: Path):
    missing = tmp_path / "groceries"

    assert load(missing / "tasks.json") == []
    assert not missing.exists()


def test_saved_tasks_load_back_equal(tmp_path: Path, two_tasks: list[Task]):
    path = tmp_path / "tasks.json"

    save(two_tasks, path)
    loaded = load(path)

    assert loaded == two_tasks
    assert loaded[0].priority is Priority.HIGH
    assert loaded[1].status is Status.DONE
    assert loaded[0].date_completed is None
    assert loaded[1].due is None


def test_an_empty_list_loads_back_empty(tmp_path: Path):
    path = tmp_path / "tasks.json"

    save([], path)

    assert load(path) == []


def test_the_file_holds_a_json_list_of_plain_records(tmp_path: Path):
    # The file is meant to be read by a person (D1), so dates are ISO 8601 text
    # (D6) and the enums are their labels.
    path = tmp_path / "tasks.json"
    task = Task(1, "Buy milk", priority=Priority.HIGH, due=DUE)

    save([task], path)

    [record] = json.loads(path.read_text(encoding="utf-8"))
    assert set(record) == RECORD_FIELDS
    assert record["id"] == 1
    assert record["name"] == "Buy milk"
    assert record["priority"] == "HIGH"
    assert record["status"] == "TO_DO"
    assert record["due"] == "2026-11-01T09:00:00"
    assert record["created"] == task.created.isoformat()
    assert record["date_completed"] is None


def test_the_file_ends_with_a_newline(tmp_path: Path):
    # A text file without one prints badly in a terminal and shows up in diffs.
    path = tmp_path / "tasks.json"

    save([], path)

    assert path.read_text(encoding="utf-8").endswith("\n")


def test_saving_creates_the_missing_directories(tmp_path: Path):
    path = tmp_path / "nested" / "dir" / "tasks.json"

    save([], path)

    assert path.is_file()

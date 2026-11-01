"""Tests for the command line: `add` and `list`."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

from datetime import datetime
from pathlib import Path

import pytest

from task_tracker import main
from task_tracker.priority import Priority
from task_tracker.storage import load, save
from task_tracker.task import Task

# D6 chose naive local time on purpose, so DTZ001 does not apply to these values.
CLOCK = datetime(2026, 10, 31, 9, 30, 0)  # noqa: DTZ001
DUE_DAY = datetime(2026, 11, 2)  # noqa: DTZ001


@pytest.fixture(name="project")
def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run from an empty directory and return where its task list will live."""
    monkeypatch.chdir(tmp_path)
    return tmp_path / "tasks.json"


@pytest.fixture
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    # Two runs of `add` a moment apart must stamp the same time, or comparing
    # the tasks they store would fail on whichever second the clock ticked over.
    monkeypatch.setattr("task_tracker.task._now", lambda: CLOCK)


def test_add_stores_a_first_task_with_id_1_and_prints_the_id(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    exit_code = main(["add", "Buy milk"])

    stored = load(project)
    assert exit_code == 0
    assert [(task.id, task.name, task.due) for task in stored] == [
        (1, "Buy milk", None)
    ]
    assert "Added task 1: Buy milk" in capsys.readouterr().out


def test_add_numbers_the_new_task_one_above_the_highest_id(project: Path):
    # Stored IDs 1 and 5: a count would give 3, a highest + 1 gives 6 (D5).
    save([Task(1, "first"), Task(5, "fifth")], project)

    main(["add", "third"])

    assert [task.id for task in load(project)] == [1, 5, 6]


def test_add_with_an_unknown_priority_exits_2_and_writes_nothing(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    with pytest.raises(SystemExit) as exit_info:
        main(["add", "Pay rent", "--priority", "URGENT"])

    assert exit_info.value.code == 2
    assert "URGENT" in capsys.readouterr().err
    assert not project.exists()


def test_add_with_a_date_that_cannot_exist_exits_2_with_an_error_line(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    with pytest.raises(SystemExit) as exit_info:
        main(["add", "Pay rent", "--due", "2026-13-45"])

    error = capsys.readouterr().err
    assert exit_info.value.code == 2
    assert "2026-13-45" in error
    assert "Traceback" not in error
    assert not project.exists()


@pytest.mark.usefixtures("fixed_clock")
def test_short_flags_store_the_same_task_as_the_long_flags(project: Path):
    main(["add", "Pay rent", "--priority", "HIGH", "--due", "2026-11-02"])
    long_form = load(project)
    project.unlink()

    main(["add", "Pay rent", "-p", "HIGH", "-D", "2026-11-02"])

    # Two runs that both dropped an option, or stored nothing, would also be
    # equal, so pin what the long form stored.
    assert len(long_form) == 1
    assert long_form[0].priority is Priority.HIGH
    assert long_form[0].due == DUE_DAY
    assert load(project) == long_form

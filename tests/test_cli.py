"""Tests for the command line: `add` and `list`."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

import errno
import io
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from task_tracker import main
from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.storage import load, save
from task_tracker.task import Task

# D6 chose naive local time on purpose, so DTZ001 does not apply to these values.
CLOCK = datetime(2026, 10, 31, 9, 30, 0)  # noqa: DTZ001
NOV_1 = datetime(2026, 11, 1)  # noqa: DTZ001
NOV_2 = datetime(2026, 11, 2)  # noqa: DTZ001
NOV_3 = datetime(2026, 11, 3)  # noqa: DTZ001
NOV_2_TIMED = datetime(2026, 11, 2, 10, 30, 45)  # noqa: DTZ001


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


@pytest.mark.parametrize("priority", ["URGENT", "high"])
def test_add_with_an_unknown_priority_exits_2_and_says_what_is_valid(
    project: Path, capsys: pytest.CaptureFixture[str], priority: str
):
    # "high" is the case-sensitive one: users type the enum names (Q1).
    with pytest.raises(SystemExit) as exit_info:
        main(["add", "Pay rent", "--priority", priority])

    # The usage line above it already lists the names, so check the error itself.
    error_line = capsys.readouterr().err.splitlines()[-1]
    assert exit_info.value.code == 2
    assert "--priority" in error_line
    assert priority in error_line
    for name in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        assert name in error_line
    assert not project.exists()


@pytest.mark.parametrize(
    "due",
    ["2026-13-45", "tomorrow", "2026-11-02T10:00:00Z", "2026-11-02T10:00:00+02:00"],
    ids=["no-such-date", "not-a-date", "utc-offset-z", "utc-offset-numeric"],
)
def test_add_with_a_bad_due_date_exits_2_naming_the_flag_and_the_format(
    project: Path, capsys: pytest.CaptureFixture[str], due: str
):
    # A UTC offset parses, but D6 stores local time only, so it is a bad value too.
    with pytest.raises(SystemExit) as exit_info:
        main(["add", "Pay rent", "--due", due])

    error = capsys.readouterr().err
    assert exit_info.value.code == 2
    error_line = error.splitlines()[-1]
    assert "--due" in error_line
    assert due in error_line
    assert "YYYY-MM-DDTHH:MM:SS" in error_line
    # Not the name of the function that did the parsing.
    assert "fromisoformat" not in error
    assert "Traceback" not in error
    assert not project.exists()


def test_add_with_a_time_of_day_keeps_the_time(project: Path):
    # Every other --due test passes a bare date, which is midnight.
    main(["add", "Pay rent", "--due", "2026-11-02T10:30:45"])

    assert load(project)[0].due == NOV_2_TIMED


def test_a_bare_command_exits_2_and_asks_for_a_command(
    capsys: pytest.CaptureFixture[str],
):
    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == 2
    assert "command" in capsys.readouterr().err.splitlines()[-1]


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
    assert long_form[0].due == NOV_2
    assert load(project) == long_form


def _listed_names(capsys: pytest.CaptureFixture[str]) -> list[str]:
    # Each line ends with the task's name, and the names used here are one word.
    return [line.split()[-1] for line in capsys.readouterr().out.splitlines()]


def test_list_shows_current_tasks_by_due_date_then_priority(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save(
        [
            Task(1, "A", due=NOV_2, priority=Priority.LOW),
            Task(2, "B", due=NOV_1, priority=Priority.LOW),
            Task(3, "C", due=NOV_1, priority=Priority.CRITICAL),
            Task(4, "D", status=Status.DONE),
            Task(5, "E", due=NOV_3, status=Status.IN_PROGRESS),
        ],
        project,
    )

    exit_code = main(["list"])

    assert exit_code == 0
    assert _listed_names(capsys) == ["C", "B", "A", "E"]


def test_list_puts_the_highest_priority_first_not_the_alphabetical_one(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    # As strings these sort CRITICAL, HIGH, LOW, MEDIUM, and they are stored in
    # the opposite of the order expected.
    save(
        [
            Task(1, "LOW", due=NOV_1, priority=Priority.LOW),
            Task(2, "MEDIUM", due=NOV_1, priority=Priority.MEDIUM),
            Task(3, "HIGH", due=NOV_1, priority=Priority.HIGH),
            Task(4, "CRITICAL", due=NOV_1, priority=Priority.CRITICAL),
        ],
        project,
    )

    main(["list"])

    assert _listed_names(capsys) == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def test_list_puts_a_task_with_no_due_date_after_one_that_has_one(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save(
        [
            Task(1, "undated", priority=Priority.MEDIUM),
            Task(2, "dated", due=NOV_1, priority=Priority.LOW),
        ],
        project,
    )

    main(["list"])

    assert _listed_names(capsys) == ["dated", "undated"]


def test_list_orders_tasks_with_no_due_date_by_priority(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save(
        [
            Task(1, "low", priority=Priority.LOW),
            Task(2, "high", priority=Priority.HIGH),
        ],
        project,
    )

    main(["list"])

    assert _listed_names(capsys) == ["high", "low"]


def test_list_orders_equal_tasks_by_id_whatever_order_the_file_holds_them(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save(
        [
            Task(2, "second", due=NOV_1, priority=Priority.HIGH),
            Task(1, "first", due=NOV_1, priority=Priority.HIGH),
        ],
        project,
    )

    main(["list"])

    assert _listed_names(capsys) == ["first", "second"]


def test_list_prints_one_line_per_task_with_id_status_priority_due_and_name(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save(
        [
            Task(3, "Walk dog"),
            Task(
                7,
                "Pay rent",
                due=NOV_2,
                priority=Priority.HIGH,
                status=Status.IN_PROGRESS,
            ),
        ],
        project,
    )

    main(["list"])

    assert [line.split() for line in capsys.readouterr().out.splitlines()] == [
        ["7", "IN_PROGRESS", "HIGH", "2026-11-02T00:00:00", "Pay", "rent"],
        ["3", "TO_DO", "LOW", "-", "Walk", "dog"],
    ]


@pytest.mark.parametrize(
    "stored",
    [[], [Task(1, "done", status=Status.DONE)]],
    ids=["no file", "only done tasks"],
)
def test_list_with_nothing_current_says_so_and_names_the_file_it_read(
    project: Path, capsys: pytest.CaptureFixture[str], stored: list[Task]
):
    # A second list started from a subdirectory explains itself (D2).
    if stored:
        save(stored, project)

    exit_code = main(["list"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "No current tasks" in out
    assert str(project) in out


def _assert_one_line_error(capsys: pytest.CaptureFixture[str], mention: str) -> None:
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("task-tracker: error: ")
    assert mention in captured.err
    # One line, and no traceback.
    assert len(captured.err.splitlines()) == 1


@pytest.mark.parametrize("argv", [["list"], ["add", "Buy milk"]])
@pytest.mark.parametrize(
    "text",
    ["not json", '[{"cls": 1}]', "[" * 200_000],
    ids=["not-json", "field-named-cls", "nested-too-deeply"],
)
def test_a_corrupt_list_file_gives_a_one_line_error_and_is_left_alone(
    project: Path, capsys: pytest.CaptureFixture[str], argv: list[str], text: str
):
    # The last two used to escape as a TypeError and a RecursionError.
    project.write_text(text, encoding="utf-8")

    exit_code = main(argv)

    assert exit_code == 1
    _assert_one_line_error(capsys, "tasks.json")
    assert project.read_text(encoding="utf-8") == text


def test_add_with_a_blank_name_gives_a_one_line_error_and_writes_nothing(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    exit_code = main(["add", ""])

    assert exit_code == 1
    _assert_one_line_error(capsys, "name")
    assert not project.exists()


def test_a_directory_where_the_list_should_be_gives_a_one_line_error(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    project.mkdir()

    exit_code = main(["list"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "tasks.json")


# --- review of PR #26: failures while writing the output ---


def _list_in_a_new_process(
    folder: Path, stdout: int, errors: Path
) -> subprocess.Popen[str]:
    """Start `task-tracker list` in `folder`; the error text goes to `errors`."""
    # The console script does the same: it passes the return value to sys.exit.
    command = "import sys, task_tracker; sys.exit(task_tracker.main(['list']))"
    with errors.open("w", encoding="utf-8") as error_file:
        child = subprocess.Popen(  # pylint: disable=consider-using-with
            [sys.executable, "-c", command],
            cwd=folder,
            stdout=stdout,
            stderr=error_file,
            text=True,
        )
    return child


def test_a_reader_that_stops_early_ends_the_list_quietly(tmp_path: Path):
    # `task-tracker list | head -1`: the reader leaves while the list is still being
    # written. 3000 lines are more than a pipe holds, so the writer notices.
    save(
        [Task(number, f"task {number}") for number in range(1, 3001)],
        tmp_path / "tasks.json",
    )
    errors = tmp_path / "errors.txt"

    child = _list_in_a_new_process(tmp_path, subprocess.PIPE, errors)
    with child:
        assert child.stdout is not None
        first_line = child.stdout.readline()
        child.stdout.close()
        child.wait(timeout=30)

    assert first_line.split()[-1] == "1"
    assert errors.read_text(encoding="utf-8") == ""
    # Python's own exit code for a broken pipe (the `signal` module's SIGPIPE note).
    assert child.returncode == 1


def test_a_pipe_that_is_already_closed_ends_a_short_list_quietly(tmp_path: Path):
    # A short list sits in the buffer until the flush, so this is the flush's test.
    save([Task(1, "Buy milk")], tmp_path / "tasks.json")
    errors = tmp_path / "errors.txt"
    read_end, write_end = os.pipe()
    os.close(read_end)

    child = _list_in_a_new_process(tmp_path, write_end, errors)
    os.close(write_end)
    with child:
        child.wait(timeout=30)

    assert errors.read_text(encoding="utf-8") == ""
    assert child.returncode == 1


def test_a_write_that_fails_after_add_saved_has_its_own_message(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    def refuse(_text: str) -> int:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(
        sys,
        "stdout",
        SimpleNamespace(encoding="utf-8", write=refuse, flush=lambda: None),
    )

    exit_code = main(["add", "Buy milk"])

    error = capsys.readouterr().err
    assert exit_code == 1
    assert error.startswith("task-tracker: error: cannot write the output: ")
    assert len(error.splitlines()) == 1
    # The task was saved before the output was written, and it stays saved.
    assert [task.name for task in load(project)] == ["Buy milk"]


# --- review of PR #26: what a name can do to the terminal ---


@pytest.mark.parametrize(
    ("name", "shown"),
    [
        ("a\nb", "a\\nb"),
        ("evil\x1b[31mRED", "evil\\x1b[31mRED"),
        ("tab\there", "tab\\there"),
        ("del\x7fchar", "del\\x7fchar"),
        ("next\x85line", "next\\x85line"),
        ("split\u2028here", "split\\u2028here"),
    ],
    ids=["newline", "escape-sequence", "tab", "delete", "c1-control", "line-separator"],
)
def test_control_characters_in_a_name_are_shown_as_escapes_on_one_line(
    project: Path, capsys: pytest.CaptureFixture[str], name: str, shown: str
):
    # A name can come from a shared file (README: lists may be shared or synced),
    # and a raw one could split a line or send an escape sequence to the terminal.
    save([Task(1, name)], project)

    main(["list"])
    listed = capsys.readouterr().out

    assert listed.splitlines() == [listed.rstrip("\n")]
    assert listed.endswith(f"  {shown}\n")
    assert "\x1b" not in listed


def test_add_shows_a_name_with_a_line_break_as_an_escape(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    main(["add", "a\nb"])

    assert capsys.readouterr().out == "Added task 1: a\\nb\n"
    assert load(project)[0].name == "a\nb"


@pytest.mark.parametrize(
    "name",
    ["Café ☕", "family 👨\u200d👩", "full\u3000width"],
    ids=["accent-and-symbol", "zero-width-joiner", "ideographic-space"],
)
def test_names_with_text_that_only_looks_unusual_are_shown_as_they_are(
    project: Path, capsys: pytest.CaptureFixture[str], name: str
):
    # Only what breaks a line or drives the terminal is escaped. A joiner inside
    # an emoji sequence and a wide space are text, and escaping them would damage
    # names that are written in other languages.
    save([Task(1, name)], project)

    main(["list"])

    assert capsys.readouterr().out.endswith(f"  {name}\n")


def test_text_that_standard_output_cannot_encode_is_shown_as_escapes(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    # PYTHONIOENCODING=ascii, or a legacy Windows code page: `print` would raise
    # UnicodeEncodeError partway through the listing.
    save([Task(1, "Zoë ☕")], project)
    buffer = io.BytesIO()
    stdout = io.TextIOWrapper(buffer, encoding="ascii")
    monkeypatch.setattr(sys, "stdout", stdout)

    exit_code = main(["list"])

    stdout.flush()
    assert exit_code == 0
    assert buffer.getvalue().endswith(b"  Zo\\xeb \\u2615\n")

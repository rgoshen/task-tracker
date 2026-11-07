"""Tests for the command line: `add` and `list`."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring

import io
import json
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from task_tracker import main
from task_tracker.cli import _discard_stdout, _printable
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
OCT_1 = datetime(2026, 10, 1)  # noqa: DTZ001
OCT_5 = datetime(2026, 10, 5)  # noqa: DTZ001
OCT_5_MORNING = datetime(2026, 10, 5, 9, 0)  # noqa: DTZ001
OCT_5_EVENING = datetime(2026, 10, 5, 17, 0)  # noqa: DTZ001
OCT_10 = datetime(2026, 10, 10)  # noqa: DTZ001


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


def test_the_top_level_help_says_list_can_show_every_task(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    # A wide terminal, so argparse does not wrap the line being checked.
    monkeypatch.setenv("COLUMNS", "200")

    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    list_line = next(
        line for line in capsys.readouterr().out.splitlines() if " list " in line
    )
    assert exit_info.value.code == 0
    assert "--all" in list_line


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


def _done(
    task_id: int, name: str, completed: datetime, due: datetime | None = None
) -> Task:
    """A DONE task completed on `completed`. Only `restore` can build a past one."""
    # The field list comes from the dataclass, so a new field needs no change here.
    # Every stamp is on or before the date completed, as `restore` requires.
    record = asdict(Task(task_id, name)) | {
        "created": OCT_1,
        "updated": completed,
        "start": OCT_1,
        "stop": OCT_1,
        "due": due,
        "status": Status.DONE,
        "date_completed": completed,
    }
    return Task.restore(record)


MAIN_CASE_ORDER = ["C", "B", "A", "E", "F", "D"]


def _save_main_case(path: Path) -> None:
    save(
        [
            Task(1, "A", due=NOV_2, priority=Priority.LOW),
            Task(2, "B", due=NOV_1, priority=Priority.LOW),
            Task(3, "C", due=NOV_1, priority=Priority.CRITICAL),
            _done(4, "D", OCT_10),
            Task(5, "E", due=NOV_3, status=Status.IN_PROGRESS),
            _done(6, "F", OCT_5),
        ],
        path,
    )


def test_list_all_shows_current_tasks_then_done_ones_by_date_completed(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    _save_main_case(project)

    exit_code = main(["list", "--all"])

    assert exit_code == 0
    assert _listed_names(capsys) == MAIN_CASE_ORDER


def test_list_all_orders_done_tasks_with_one_date_completed_by_id(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    # Stored higher ID first, so the file order would give the other answer.
    save([_done(2, "second", OCT_5), _done(1, "first", OCT_5)], project)

    main(["list", "--all"])

    assert _listed_names(capsys) == ["first", "second"]


def test_list_all_orders_done_tasks_completed_on_one_day_by_the_time(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    # The lower ID finished later, so the ID tie-break would give the other answer.
    save([_done(1, "late", OCT_5_EVENING), _done(2, "early", OCT_5_MORNING)], project)

    main(["list", "--all"])

    assert _listed_names(capsys) == ["early", "late"]


def test_list_all_reports_a_done_task_without_a_date_completed_as_one_line(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    # `load` refuses such a record, so the broken task is handed over directly. It
    # stands for a rule `Task` breaks one day, and the sort must not hide it.
    broken = Task(7, "broken")
    broken.status = Status.DONE
    monkeypatch.setattr("task_tracker.cli.load", lambda _path: [broken])

    exit_code = main(["list", "--all"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "task 7")


def test_list_all_puts_done_task_due_first_after_every_current_task(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save([_done(1, "done", OCT_5, due=OCT_1), Task(2, "open", due=NOV_1)], project)

    main(["list", "--all"])

    assert _listed_names(capsys) == ["open", "done"]


def test_list_all_lists_only_done_tasks_while_plain_list_says_none_current(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save([_done(1, "old", OCT_5)], project)

    main(["list"])
    plain = capsys.readouterr().out
    main(["list", "--all"])

    assert f"No current tasks in {project}" in plain
    assert _listed_names(capsys) == ["old"]


@pytest.mark.parametrize("flag", ["-a", "--all"])
def test_list_short_and_long_all_flags_show_the_same_order(
    project: Path, capsys: pytest.CaptureFixture[str], flag: str
):
    _save_main_case(project)

    main(["list", flag])

    assert _listed_names(capsys) == MAIN_CASE_ORDER


@pytest.mark.parametrize("stored", [None, []], ids=["no file", "empty file"])
def test_list_all_with_no_tasks_says_no_tasks_and_names_the_file(
    project: Path, capsys: pytest.CaptureFixture[str], stored: list[Task] | None
):
    if stored is not None:
        save(stored, project)

    exit_code = main(["list", "--all"])

    assert exit_code == 0
    assert capsys.readouterr().out == f"No tasks in {project}\n"


def test_list_shows_current_tasks_by_due_date_then_priority(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    _save_main_case(project)

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


def _assert_one_line_error(capsys: pytest.CaptureFixture[str], mention: str) -> str:
    """Check the error that was printed and return it for further checks."""
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("task-tracker: error: ")
    assert mention in captured.err
    # One line, and no traceback.
    assert len(captured.err.splitlines()) == 1
    return captured.err


@pytest.mark.parametrize("argv", [["list"], ["list", "--all"], ["add", "Buy milk"]])
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


def test_a_key_in_a_stored_record_cannot_drive_the_terminal_through_the_error(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    # "unknown field(s)" repeats the record's own keys. The file may be shared, so a
    # key with an escape sequence and a line break must not reach the terminal raw.
    save([Task(1, "x")], project)
    records = json.loads(project.read_text(encoding="utf-8"))
    records[0]["key\x1b[2J\nsecond line"] = 1
    project.write_text(json.dumps(records), encoding="utf-8")

    exit_code = main(["list"])

    assert exit_code == 1
    error = _assert_one_line_error(capsys, "unknown field")
    assert "\x1b" not in error
    assert "key\\x1b[2J\\nsecond line" in error


def test_an_error_has_nowhere_to_go_when_standard_error_is_closed(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    # `print(file=None)` writes to standard output, which would put an error into
    # the output that another program is reading.
    project.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(sys, "stderr", None)

    exit_code = main(["list"])

    assert exit_code == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("name", "mention"),
    [("", "name must not be blank"), ("bad \udcff", "name must be valid UTF-8 text")],
    ids=["blank", "not-valid-utf-8"],
)
def test_add_with_a_name_that_cannot_be_kept_gives_a_one_line_error_and_writes_nothing(
    project: Path, capsys: pytest.CaptureFixture[str], name: str, mention: str
):
    # A byte that is not valid UTF-8 on the command line reaches Python as a lone
    # surrogate, and `save` writes UTF-8, so the name is refused before any file.
    exit_code = main(["add", name])

    assert exit_code == 1
    _assert_one_line_error(capsys, mention)
    assert not project.exists()


def test_a_directory_where_the_list_should_be_gives_a_one_line_error(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    project.mkdir()

    exit_code = main(["list"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "tasks.json")


# --- review of PR #26: failures while writing the output ---


_ERRORS_FILE = "errors.txt"


@contextmanager
def _run_in_a_new_process(
    folder: Path, argv: list[str], stdout: int, *, close_stdout: bool = False
) -> Iterator[subprocess.Popen[str]]:
    """Run `task-tracker` with `argv` in `folder`; wait for it when the block ends.

    Its standard error goes to `errors.txt` in `folder`, so a test reads exactly
    what a terminal would have shown. With `close_stdout` the shell closes
    descriptor 1 before it starts the program, as cron and some service managers
    do, and `stdout` is not used.
    """
    # The console script does the same: it passes the return value to sys.exit.
    code = "import sys, task_tracker; sys.exit(task_tracker.main(sys.argv[1:]))"
    command = [sys.executable, "-c", code, *argv]
    if close_stdout:
        command = ["sh", "-c", 'exec "$@" >&-', "sh", *command]
    with (
        (folder / _ERRORS_FILE).open("w", encoding="utf-8") as error_file,
        subprocess.Popen(
            command,
            cwd=folder,
            stdout=stdout,
            stderr=error_file,
            text=True,
        ) as child,
    ):
        yield child


def test_a_reader_that_stops_early_ends_the_list_quietly(tmp_path: Path):
    # `task-tracker list | head -1`: the reader leaves while the list is still being
    # written. 3000 lines are more than a pipe holds, so the writer notices.
    save(
        [Task(number, f"task {number}") for number in range(1, 3001)],
        tmp_path / "tasks.json",
    )

    with _run_in_a_new_process(tmp_path, ["list"], subprocess.PIPE) as child:
        assert child.stdout is not None
        first_line = child.stdout.readline()
        child.stdout.close()
        child.wait(timeout=30)

    assert first_line.split()[-1] == "1"
    assert (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8") == ""
    # Python's own exit code for a broken pipe (the `signal` module's SIGPIPE note).
    assert child.returncode == 1


def test_a_pipe_that_is_already_closed_ends_a_short_list_quietly(tmp_path: Path):
    # A short list sits in the buffer until the flush, so this is the flush's test.
    save([Task(1, "Buy milk")], tmp_path / "tasks.json")
    read_end, write_end = os.pipe()
    os.close(read_end)

    with _run_in_a_new_process(tmp_path, ["list"], write_end) as child:
        os.close(write_end)
        child.wait(timeout=30)

    assert (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8") == ""
    assert child.returncode == 1


# Each command, and the task names the file holds after it ran: `add` saves.
_BOTH_COMMANDS = pytest.mark.parametrize(
    ("argv", "stored"),
    [(["list"], ["first"]), (["add", "second"], ["first", "second"])],
    ids=["list", "add"],
)


@pytest.mark.skipif(sys.platform == "win32", reason="needs a read-only descriptor")
@_BOTH_COMMANDS
def test_a_write_that_fails_ends_with_one_error_line_and_exit_1(
    tmp_path: Path, argv: list[str], stored: list[str]
):
    # Standard output is a descriptor opened for reading only, so every write to it
    # fails with EBADF: an OSError that is not a broken pipe. A fake `sys.stdout`
    # would have no buffer for Python to flush again at exit, which is where exit
    # code 120 and the "Exception ignored" lines came from.
    save([Task(1, "first")], tmp_path / "tasks.json")
    sink = tmp_path / "sink.txt"
    sink.write_text("", encoding="utf-8")
    read_only = os.open(sink, os.O_RDONLY)
    try:
        with _run_in_a_new_process(tmp_path, argv, read_only) as child:
            child.wait(timeout=30)
    finally:
        os.close(read_only)

    error_lines = (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8").splitlines()
    assert child.returncode == 1
    assert len(error_lines) == 1
    assert error_lines[0].startswith("task-tracker: error: cannot write the output: ")
    # `add` saves before it prints, and the task stays saved.
    assert [task.name for task in load(tmp_path / "tasks.json")] == stored


@pytest.mark.skipif(sys.platform == "win32", reason="needs sh to close descriptor 1")
@_BOTH_COMMANDS
def test_a_closed_standard_output_is_not_an_error(
    tmp_path: Path, argv: list[str], stored: list[str]
):
    # With descriptor 1 closed, `sys.stdout` is None. `print` takes that to mean
    # "nowhere to write", so the command has nothing to complain about.
    save([Task(1, "first")], tmp_path / "tasks.json")

    with _run_in_a_new_process(
        tmp_path, argv, subprocess.DEVNULL, close_stdout=True
    ) as child:
        child.wait(timeout=30)

    assert (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8") == ""
    assert child.returncode == 0
    assert [task.name for task in load(tmp_path / "tasks.json")] == stored


@pytest.fixture(name="stdout_file")
def _stdout_file(tmp_path: Path) -> Iterator[tuple[int, Path]]:
    """A real descriptor on a file that the test can read."""
    path = tmp_path / "stdout.txt"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT)
    yield descriptor, path
    os.close(descriptor)


def _become_stdout(monkeypatch: pytest.MonkeyPatch, descriptor: int) -> None:
    # Call this in the test body, not in a fixture: pytest's capture puts its own
    # stream back into `sys.stdout` when the body starts, which would replace this
    # one, and the helper would redirect the capture file instead.
    monkeypatch.setattr(sys, "stdout", SimpleNamespace(fileno=lambda: descriptor))


def test_discarding_standard_output_sends_later_writes_to_devnull(
    stdout_file: tuple[int, Path], monkeypatch: pytest.MonkeyPatch
):
    descriptor, path = stdout_file
    _become_stdout(monkeypatch, descriptor)

    _discard_stdout()
    os.write(descriptor, b"the flush at exit")

    assert path.read_bytes() == b""


def test_discarding_standard_output_leaves_no_descriptor_open(
    stdout_file: tuple[int, Path], monkeypatch: pytest.MonkeyPatch
):
    descriptor, _ = stdout_file
    _become_stdout(monkeypatch, descriptor)
    # `dup` returns the lowest free number, which is where `os.open` would put the
    # helper's own descriptor. If the helper keeps it, the lowest free number moves.
    lowest_free = os.dup(descriptor)
    os.close(lowest_free)

    _discard_stdout()

    still_lowest = os.dup(descriptor)
    os.close(still_lowest)
    assert still_lowest == lowest_free


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
        ("a\u202eb", "a\\u202eb"),
        ("a\u2066b", "a\\u2066b"),
        ("a\u200eb", "a\\u200eb"),
        ("a\u061cb", "a\\u061cb"),
    ],
    ids=[
        "newline",
        "escape-sequence",
        "tab",
        "delete",
        "c1-control",
        "line-separator",
        "right-to-left-override",
        "isolate",
        "left-to-right-mark",
        "arabic-letter-mark",
    ],
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


@pytest.mark.parametrize(
    "char",
    [
        "\x00",
        "\x1f",
        "\x7f",
        "\x80",
        "\x9f",
        "\u2028",
        "\u2029",
        "\u061c",
        "\u200e",
        "\u200f",
        "\u202a",
        "\u202e",
        "\u2066",
        "\u2069",
    ],
    ids=[
        "nul",
        "unit-separator",
        "delete",
        "first-c1",
        "last-c1",
        "line",
        "paragraph",
        "arabic-letter-mark",
        "left-to-right-mark",
        "right-to-left-mark",
        "first-embedding",
        "last-override",
        "first-isolate",
        "last-isolate",
    ],
)
def test_the_first_and_last_character_of_each_escaped_range_is_escaped(char: str):
    escape = char.encode("unicode_escape").decode("ascii")

    assert _printable(f"a{char}b", io.StringIO()) == f"a{escape}b"


@pytest.mark.parametrize(
    "char",
    [" ", "~", "\xa0", "\u2027", "\u202f", "\u061b", "\u061d", "\u200d", "\u2010"],
    ids=[
        "space",
        "tilde",
        "no-break-space",
        "hyphenation-point",
        "narrow-no-break",
        "arabic-semicolon",
        "arabic-end-of-text",
        "zero-width-joiner",
        "hyphen",
    ],
)
def test_the_character_next_to_an_escaped_range_is_left_alone(char: str):
    assert _printable(f"a{char}b", io.StringIO()) == f"a{char}b"


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

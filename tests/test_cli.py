"""Tests for the command line: the five commands and the options that pick a list."""

# Test names state the intent, so per-test docstrings would only repeat them.
# pylint: disable=missing-function-docstring
# The command tests share fixtures and helpers, so they stay in this one module.
# pylint: disable=too-many-lines

import io
import json
import os
import subprocess
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timedelta
from itertools import takewhile
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
OCT_1_NINE = datetime(2026, 10, 1, 9, 0)  # noqa: DTZ001
DEC_1 = datetime(2026, 12, 1)  # noqa: DTZ001


@pytest.fixture(name="project")
def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run from an empty directory and return where its task list will live."""
    monkeypatch.chdir(tmp_path)
    return tmp_path / "tasks.json"


@pytest.fixture(name="home", autouse=True)
def _home(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Point HOME at an empty directory outside the cwd and return it.

    Autouse, so no test in this module can reach the real home directory.
    `Path.home()` reads HOME first on POSIX (via `os.path.expanduser`).
    """
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    return home


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


def _stored(
    task_id: int,
    name: str,
    *,
    priority: Priority = Priority.LOW,
    due: datetime | None = None,
    date_completed: datetime | None = None,
) -> Task:
    """A task stored on 2026-10-01 at 09:00, DONE when it has a date completed."""
    # The field list comes from the dataclass, so a new field needs no change here.
    # Every stamp is on or before the date completed, as `restore` requires.
    record = asdict(Task(task_id, name)) | {
        "created": OCT_1_NINE,
        "updated": OCT_1_NINE,
        "start": OCT_1_NINE,
        "stop": OCT_1_NINE,
        "priority": priority,
        "status": Status.TO_DO if date_completed is None else Status.DONE,
        "due": due,
        "date_completed": date_completed,
    }
    return Task.restore(record)


def _done(
    task_id: int, name: str, completed: datetime, due: datetime | None = None
) -> Task:
    """A DONE task completed on `completed`. Only `restore` can build a past one."""
    return _stored(task_id, name, due=due, date_completed=completed)


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


@pytest.mark.parametrize(
    "argv",
    [
        ["list"],
        ["list", "--all"],
        ["add", "Buy milk"],
        ["update", "1", "--name", "x"],
        ["delete", "1"],
    ],
    ids=["list", "list-all", "add", "update", "delete"],
)
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


@pytest.mark.parametrize(
    "argv",
    [["list"], ["update", "1", "--name", "x"], ["delete", "1"]],
    ids=["list", "update", "delete"],
)
def test_a_directory_where_the_list_should_be_gives_a_one_line_error(
    project: Path, capsys: pytest.CaptureFixture[str], argv: list[str]
):
    project.mkdir()

    exit_code = main(argv)

    assert exit_code == 1
    _assert_one_line_error(capsys, "tasks.json")


# --- review of PR #26: failures while writing the output ---


_ERRORS_FILE = "errors.txt"


@contextmanager
def _run_in_a_new_process(
    folder: Path,
    argv: list[str],
    stdout: int,
    *,
    close_stdout: bool = False,
    stdin: int = subprocess.DEVNULL,
) -> Iterator[subprocess.Popen[str]]:
    """Run `task-tracker` with `argv` in `folder`; wait for it when the block ends.

    Its standard error goes to `errors.txt` in `folder`, so a test reads exactly
    what a terminal would have shown. Its standard input is empty unless `stdin`
    says otherwise. With `close_stdout` the shell closes descriptor 1 before it
    starts the program, as cron and some service managers do, and `stdout` is not
    used.
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
            stdin=stdin,
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


def test_an_error_after_a_prompt_nobody_could_read_still_exits_1_without_a_second_error(
    tmp_path: Path,
):
    # `input` writes the prompt to a pipe whose reader has gone, swallows the flush
    # error, and leaves the bytes in the buffer. When the command then ends with an
    # error, the flush at exit failed again: "Exception ignored" and exit code 120.
    save([Task(1, "Buy milk")], tmp_path / "tasks.json")
    read_end, write_end = os.pipe()
    os.close(read_end)

    with _run_in_a_new_process(tmp_path, ["delete", "1"], write_end) as child:
        os.close(write_end)
        child.wait(timeout=30)

    error = (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8")
    assert child.returncode == 1
    assert error == (
        "task-tracker: error: no answer to the prompt: task 1 was not deleted\n"
    )


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


# --- M5: update ---


@pytest.mark.usefixtures("fixed_clock")
def test_update_changes_the_name_and_priority_of_the_given_task_only(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save(
        [_stored(1, "Buy milk"), _stored(2, "Walk dog", priority=Priority.HIGH)],
        project,
    )
    other_before = load(project)[1]

    exit_code = main(["update", "1", "--name", "Buy oat milk", "--priority", "HIGH"])

    changed, other = load(project)
    assert exit_code == 0
    assert capsys.readouterr().out == "Updated task 1: Buy oat milk\n"
    assert (changed.name, changed.priority) == ("Buy oat milk", Priority.HIGH)
    assert (changed.created, changed.updated) == (OCT_1_NINE, CLOCK)
    assert other == other_before


@pytest.mark.usefixtures("fixed_clock")
def test_update_to_done_sets_date_completed_to_the_clock(project: Path):
    save([_stored(1, "Buy milk")], project)

    main(["update", "1", "--status", "DONE"])

    stored = load(project)[0]
    assert (stored.status, stored.date_completed) == (Status.DONE, CLOCK)


@pytest.mark.usefixtures("fixed_clock")
@pytest.mark.parametrize("status", ["TO_DO", "IN_PROGRESS"])
def test_update_away_from_done_clears_date_completed(project: Path, status: str):
    save([_done(1, "Buy milk", OCT_5)], project)

    exit_code = main(["update", "1", "--status", status])

    stored = load(project)[0]
    assert exit_code == 0
    assert (stored.status, stored.date_completed) == (Status(status), None)
    assert stored.updated == CLOCK


@pytest.mark.usefixtures("fixed_clock")
@pytest.mark.parametrize(
    ("long_form", "short_form"),
    [
        (["--name", "Buy oat milk"], ["-n", "Buy oat milk"]),
        (["--priority", "HIGH"], ["-p", "HIGH"]),
        (["--status", "IN_PROGRESS"], ["-s", "IN_PROGRESS"]),
        (["--due", "2026-12-01"], ["-D", "2026-12-01"]),
        (["--clear-due"], ["-C"]),
    ],
    ids=["name", "priority", "status", "due", "clear-due"],
)
def test_each_short_option_leaves_the_same_file_as_its_long_form(
    project: Path, long_form: list[str], short_form: list[str]
):
    seed = [_stored(1, "Buy milk", due=NOV_1)]
    save(seed, project)
    seeded = project.read_bytes()

    main(["update", "1", *long_form])
    from_long = project.read_bytes()
    save(seed, project)
    main(["update", "1", *short_form])

    assert from_long != seeded  # else two runs that did nothing would match
    assert project.read_bytes() == from_long


@pytest.mark.usefixtures("fixed_clock")
@pytest.mark.parametrize(
    ("argv", "due"),
    [(["--due", "2026-12-01"], DEC_1), (["--clear-due"], None)],
    ids=["sets-midnight", "clears"],
)
def test_due_sets_the_given_date_at_midnight_or_clears_it(
    project: Path, argv: list[str], due: datetime | None
):
    save([_stored(1, "Buy milk", due=NOV_1)], project)

    main(["update", "1", *argv])

    assert load(project)[0].due == due


def test_due_and_clear_due_together_exit_2_and_leave_the_file_unchanged(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save([_stored(1, "Buy milk", due=NOV_1)], project)
    before = project.read_bytes()

    with pytest.raises(SystemExit) as exit_info:
        main(["update", "1", "--due", "2026-12-01", "--clear-due"])

    assert exit_info.value.code == 2
    assert "not allowed with" in capsys.readouterr().err
    assert project.read_bytes() == before


# Each (name, text) pair is an ID that `_task_id` refuses. Shared by `update` and
# `delete`, so both commands are checked against one list.
BAD_ID_CASES = [
    ("id-word", "one"),
    ("id-part", "1.5"),
    ("id-plus-sign", "+1"),
    ("id-underscore", "0_1"),
    ("id-spaces", " 1 "),
    ("id-arabic-indic-digit", "\u0661"),
    ("id-negative", "-1"),
    ("id-zero", "0"),
]


@pytest.mark.parametrize(
    ("argv", "mention"),
    [
        (["1", "--status", "DOING"], "--status"),
        (["1", "--priority", "URGENT"], "--priority"),
        (["1", "--due", "tomorrow"], "--due"),
        *[([text, "--name", "x"], "whole number") for _, text in BAD_ID_CASES],
    ],
    ids=[
        "unknown-status",
        "unknown-priority",
        "due-not-a-date",
        *[name for name, _ in BAD_ID_CASES],
    ],
)
def test_a_bad_option_value_exits_2_naming_it_and_leaves_the_file_unchanged(
    project: Path, capsys: pytest.CaptureFixture[str], argv: list[str], mention: str
):
    save([_stored(1, "Buy milk")], project)
    before = project.read_bytes()

    with pytest.raises(SystemExit) as exit_info:
        main(["update", *argv])

    assert exit_info.value.code == 2
    assert mention in capsys.readouterr().err.splitlines()[-1]
    assert project.read_bytes() == before


@pytest.mark.parametrize(
    "argv", [["--name", "Landed"], ["--status", "DONE"]], ids=["rename", "done"]
)
def test_update_works_when_the_clock_is_behind_the_stored_time(
    project: Path, monkeypatch: pytest.MonkeyPatch, argv: list[str]
):
    # A time zone change can put the clock hours behind the task's own stamps.
    later = CLOCK + timedelta(hours=13)
    monkeypatch.setattr("task_tracker.task._now", lambda: later)
    save([Task(1, "Fly home")], project)
    monkeypatch.setattr("task_tracker.task._now", lambda: CLOCK)

    exit_code = main(["update", "1", *argv])

    assert exit_code == 0
    assert load(project)[0].updated == later


@pytest.mark.usefixtures("fixed_clock")
def test_a_blank_name_exits_1_with_one_error_line_and_leaves_the_file_unchanged(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save([_stored(1, "Buy milk")], project)
    before = project.read_bytes()

    exit_code = main(["update", "1", "--name", "   "])

    assert exit_code == 1
    _assert_one_line_error(capsys, "name must not be blank")
    assert project.read_bytes() == before


@pytest.mark.usefixtures("fixed_clock")
def test_values_a_task_already_has_leave_the_file_unchanged(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    # A file `save` wrote would come out the same if it were rewritten, so the test
    # could not tell. This layout is not the one `save` writes.
    save([_stored(1, "Buy milk")], project)
    records = json.loads(project.read_text(encoding="utf-8"))
    project.write_text(json.dumps(records, indent=4), encoding="utf-8")
    before = project.read_bytes()

    exit_code = main(["update", "1", "--name", "Buy milk", "--priority", "LOW"])

    assert exit_code == 0
    assert capsys.readouterr().out == "No change to task 1: Buy milk\n"
    assert project.read_bytes() == before


NOTHING_TO_UPDATE = (
    "nothing to update: give at least one of --name, --priority, --status, --due, "
    "--clear-due"
)


def test_update_of_a_missing_id_exits_1_naming_it_and_leaves_the_file_unchanged(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    save([_stored(1, "Buy milk")], project)
    before = project.read_bytes()

    exit_code = main(["update", "99", "--name", "x"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "no task with ID 99")
    assert project.read_bytes() == before


def test_update_with_no_tasks_file_exits_1_and_creates_no_file(
    project: Path, capsys: pytest.CaptureFixture[str]
):
    exit_code = main(["update", "1", "--name", "x"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "no task with ID 1")
    assert not project.exists()


@pytest.mark.parametrize("id_text", ["1", "99"])
def test_update_with_no_option_exits_1_naming_the_options_and_leaves_the_file_alone(
    project: Path, capsys: pytest.CaptureFixture[str], id_text: str
):
    # The option check comes first, so an ID that does not exist is not reported.
    save([_stored(1, "Buy milk")], project)
    before = project.read_bytes()

    exit_code = main(["update", id_text])

    assert exit_code == 1
    _assert_one_line_error(capsys, NOTHING_TO_UPDATE)
    assert project.read_bytes() == before


@pytest.mark.parametrize(
    ("argument", "explanation"),
    [
        ("id", "ID of the task to change"),
        ("--name", "new name"),
        ("--priority", "new priority"),
        ("--status", "new status"),
        ("--due", "YYYY-MM-DD"),
        ("--clear-due", "remove the due date"),
    ],
)
def test_update_help_explains_each_argument(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    argument: str,
    explanation: str,
):
    # A wide terminal keeps the explanations on one line. argparse still moves the
    # text of a long option such as `--priority {CRITICAL,...}` to the next line, so
    # the row is read together with the lines indented under it.
    monkeypatch.setenv("COLUMNS", "200")

    with pytest.raises(SystemExit) as exit_info:
        main(["update", "--help"])

    lines = capsys.readouterr().out.splitlines()
    start = next(
        n for n, line in enumerate(lines) if line.lstrip().startswith(argument)
    )
    row = [lines[start]]
    row += list(takewhile(lambda line: line.startswith(" " * 10), lines[start + 1 :]))
    assert exit_info.value.code == 0
    assert explanation in " ".join(" ".join(row).split())


# --- M6: delete ---


def _answer_with(monkeypatch: pytest.MonkeyPatch, reply: str) -> list[str]:
    """Patch `input` to answer `reply`; return the list that collects each prompt."""
    prompts: list[str] = []

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return reply

    monkeypatch.setattr("builtins.input", fake_input)
    return prompts


def _save_three(path: Path) -> None:
    save([_stored(1, "Buy milk"), _stored(2, "Walk dog"), _stored(3, "Pay rent")], path)


def _records(path: Path) -> list[dict[str, object]]:
    """The stored records as written, so a comparison is of the file itself."""
    return json.loads(path.read_text(encoding="utf-8"))


def test_delete_yes_removes_only_the_named_task(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    # Given three stored tasks and a person who answers yes
    _save_three(project)
    before = _records(project)
    _answer_with(monkeypatch, "y")

    # When task 2 is deleted
    exit_code = main(["delete", "2"])

    # Then tasks 1 and 3 are stored exactly as they were
    assert exit_code == 0
    assert capsys.readouterr().out == "Deleted task 2: Walk dog\n"
    assert _records(project) == [before[0], before[2]]


def test_delete_no_keeps_every_task_and_leaves_the_file_bytes_alone(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    # Hand-formatted with indent=4, which `save` never writes: a rewrite would change
    # the bytes, so an unchanged file proves the file was not written.
    _save_three(project)
    project.write_text(json.dumps(_records(project), indent=4), encoding="utf-8")
    before = project.read_bytes()
    _answer_with(monkeypatch, "n")

    exit_code = main(["delete", "2"])

    assert exit_code == 0
    assert capsys.readouterr().out == "Kept task 2: Walk dog\n"
    assert project.read_bytes() == before


@pytest.mark.parametrize("reply", ["y", "n"])
def test_delete_asks_with_the_id_and_the_name_before_it_changes_anything(
    project: Path, monkeypatch: pytest.MonkeyPatch, reply: str
):
    _save_three(project)
    prompts = _answer_with(monkeypatch, reply)

    main(["delete", "2"])

    assert prompts == ["Delete task 2: Walk dog? [y/N] "]


@pytest.mark.parametrize(
    ("reply", "deleted"),
    [
        ("y", True),
        ("Y", True),
        ("yes", True),
        ("YES", True),
        ("  yes  ", True),
        ("n", False),
        ("no", False),
        ("", False),
        ("maybe", False),
        ("yy", False),
    ],
    ids=["y", "Y", "yes", "YES", "padded-yes", "n", "no", "empty", "maybe", "yy"],
)
def test_only_a_yes_deletes_the_task(
    project: Path, monkeypatch: pytest.MonkeyPatch, reply: str, deleted: bool
):
    _save_three(project)
    _answer_with(monkeypatch, reply)

    exit_code = main(["delete", "2"])

    assert exit_code == 0
    assert [task.id for task in load(project)] == ([1, 3] if deleted else [1, 2, 3])


def test_a_control_character_in_the_name_is_shown_as_an_escape_on_one_line(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    save([_stored(1, "Buy\nmilk")], project)
    prompts = _answer_with(monkeypatch, "n")

    main(["delete", "1"])

    assert prompts == ["Delete task 1: Buy\\nmilk? [y/N] "]


def test_deleting_the_only_task_leaves_an_empty_list_that_list_reports(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    save([_stored(1, "Buy milk")], project)
    _answer_with(monkeypatch, "y")

    assert main(["delete", "1"]) == 0
    assert _records(project) == []
    capsys.readouterr()

    assert main(["list"]) == 0
    assert "No current tasks in" in capsys.readouterr().out


def _never_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch `input` so that any call fails the test."""

    def fail(prompt: str = "") -> str:
        # A plain `raise`, not `pytest.fail`: the CI type checker runs without pytest
        # installed, sees `pytest.fail` as `Any`, and then reports a missing return.
        # `main` catches only `ValueError` and `OSError`, so this reaches the test.
        raise AssertionError(f"input was called with {prompt!r}")

    monkeypatch.setattr("builtins.input", fail)


def test_delete_of_a_missing_id_exits_1_naming_it_and_never_asks(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    _save_three(project)
    before = project.read_bytes()
    _never_asked(monkeypatch)

    exit_code = main(["delete", "99"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "no task with ID 99")
    assert project.read_bytes() == before


def test_delete_with_no_tasks_file_exits_1_and_creates_no_file(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    _never_asked(monkeypatch)

    exit_code = main(["delete", "1"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "no task with ID 1")
    assert not project.exists()


@pytest.mark.parametrize(
    "id_text",
    [text for _, text in BAD_ID_CASES],
    ids=[name for name, _ in BAD_ID_CASES],
)
def test_delete_with_a_bad_id_exits_2_and_never_asks(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    id_text: str,
):
    _save_three(project)
    before = project.read_bytes()
    _never_asked(monkeypatch)

    with pytest.raises(SystemExit) as exit_info:
        main(["delete", id_text])

    assert exit_info.value.code == 2
    assert "whole number" in capsys.readouterr().err.splitlines()[-1]
    assert project.read_bytes() == before


@pytest.mark.parametrize(
    "error",
    [
        EOFError(),
        KeyboardInterrupt(),
        # Standard input that is not UTF-8: `input` raises a ValueError, which
        # `main` would otherwise print as a codec message with no word on the task.
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
    ],
    ids=["end-of-input", "ctrl-c", "not-utf-8"],
)
def test_a_prompt_that_gets_no_answer_deletes_nothing_and_says_so_in_one_line(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: BaseException,
):
    _save_three(project)
    before = project.read_bytes()

    def no_answer(prompt: str = "") -> str:
        raise error

    monkeypatch.setattr("builtins.input", no_answer)

    exit_code = main(["delete", "2"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "task 2 was not deleted")
    assert project.read_bytes() == before


class _Terminal(io.StringIO):
    """Standard input that claims to be a terminal, as it is for a person typing."""

    def isatty(self) -> bool:
        return True


@pytest.mark.parametrize(
    "error", [EOFError(), KeyboardInterrupt()], ids=["ctrl-d", "ctrl-c"]
)
def test_on_a_terminal_the_no_answer_error_starts_on_its_own_line(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: BaseException,
):
    # The terminal echoes `^C` or `^D` after the prompt and leaves the cursor there,
    # so an error written at once would run on from the prompt (checked in a pty).
    _save_three(project)

    def no_answer(prompt: str = "") -> str:
        raise error

    monkeypatch.setattr("builtins.input", no_answer)
    monkeypatch.setattr(sys, "stdin", _Terminal())

    exit_code = main(["delete", "2"])

    assert exit_code == 1
    assert capsys.readouterr().err == (
        "\ntask-tracker: error: no answer to the prompt: task 2 was not deleted\n"
    )


@pytest.mark.parametrize("stream", ["stdin", "stdout", "stderr"])
def test_a_closed_standard_stream_deletes_nothing_without_asking(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stream: str,
):
    # With descriptor 0, 1 or 2 closed at start-up the matching `sys` stream is
    # `None`, and the real `input` would raise RuntimeError ("lost sys.stdin").
    _save_three(project)
    before = project.read_bytes()
    _never_asked(monkeypatch)
    errors_are_visible = stream != "stderr"
    monkeypatch.setattr(sys, stream, None)

    exit_code = main(["delete", "2"])

    assert exit_code == 1
    if errors_are_visible:
        _assert_one_line_error(capsys, "task 2 was not deleted")
    assert project.read_bytes() == before


def test_a_runtime_error_that_is_not_a_closed_stream_is_not_called_no_answer(
    project: Path, monkeypatch: pytest.MonkeyPatch
):
    # A bug inside `input` must stay visible as the bug it is, not become a polite
    # "no answer": only the three closed streams are known and handled.
    _save_three(project)

    def broken_input(prompt: str = "") -> str:
        raise RuntimeError("something else broke")

    monkeypatch.setattr("builtins.input", broken_input)

    with pytest.raises(RuntimeError, match="something else broke"):
        main(["delete", "2"])


def test_delete_with_standard_input_at_its_end_gives_one_error_line(tmp_path: Path):
    # A real process with standard input at `/dev/null`, as a script or cron runs it.
    save([Task(1, "Buy milk")], tmp_path / "tasks.json")
    before = (tmp_path / "tasks.json").read_bytes()

    with _run_in_a_new_process(tmp_path, ["delete", "1"], subprocess.DEVNULL) as child:
        child.wait(timeout=30)

    error = (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8")
    assert child.returncode == 1
    assert error == (
        "task-tracker: error: no answer to the prompt: task 1 was not deleted\n"
    )
    assert (tmp_path / "tasks.json").read_bytes() == before


def test_a_task_added_while_the_prompt_is_open_survives_the_delete(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    # Given another writer that adds task 4 while the prompt waits for a person
    _save_three(project)

    def another_writer_adds_task_4(_prompt: str = "") -> str:
        save([*load(project), _stored(4, "Read book")], project)
        return "y"

    monkeypatch.setattr("builtins.input", another_writer_adds_task_4)

    # When task 2 is deleted after the yes
    exit_code = main(["delete", "2"])

    # Then task 4 is kept and only task 2 is gone
    assert exit_code == 0
    assert capsys.readouterr().out == "Deleted task 2: Walk dog\n"
    assert [task.id for task in load(project)] == [1, 3, 4]


@pytest.mark.parametrize(
    "others_tasks",
    [
        [(1, "Buy milk"), (2, "Walk cat"), (3, "Pay rent")],
        [(1, "Buy milk"), (3, "Pay rent")],
    ],
    ids=["renamed", "removed"],
)
def test_a_task_changed_while_the_prompt_is_open_is_not_deleted(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    others_tasks: list[tuple[int, str]],
):
    # Given another writer that renames or removes task 2 while the prompt is open
    _save_three(project)
    written: list[bytes] = []

    def another_writer_changes_task_2(_prompt: str = "") -> str:
        save([_stored(number, name) for number, name in others_tasks], project)
        written.append(project.read_bytes())
        return "y"

    monkeypatch.setattr("builtins.input", another_writer_changes_task_2)

    exit_code = main(["delete", "2"])

    # Then the delete refuses, says so in one line, and leaves that writer's file
    assert exit_code == 1
    _assert_one_line_error(
        capsys, "task 2 changed or was removed while the prompt was open"
    )
    assert project.read_bytes() == written[0]


def _make_corrupt(path: Path) -> None:
    path.write_text("not json", encoding="utf-8")


def _make_a_directory(path: Path) -> None:
    path.unlink()
    path.mkdir()


def _snapshot(path: Path) -> bytes | None:
    """The bytes of a list file, or None once it has become a directory."""
    return path.read_bytes() if path.is_file() else None


@pytest.mark.parametrize(
    "break_the_list",
    [_make_corrupt, _make_a_directory],
    ids=["corrupt", "directory"],
)
def test_a_list_that_cannot_be_read_after_the_answer_gives_one_error_line(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    break_the_list: Callable[[Path], None],
):
    # Given another writer that breaks the list while the prompt is open
    _save_three(project)
    left: list[bytes | None] = []

    def another_writer_breaks_the_list(_prompt: str = "") -> str:
        break_the_list(project)
        left.append(_snapshot(project))
        return "y"

    monkeypatch.setattr("builtins.input", another_writer_breaks_the_list)

    exit_code = main(["delete", "2"])

    # Then the second read fails like any other: one line, and that file is left
    assert exit_code == 1
    _assert_one_line_error(capsys, "tasks.json")
    assert _snapshot(project) == left[0]


def test_a_save_that_fails_leaves_the_list_as_it_was_and_gives_one_error_line(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    _save_three(project)
    before = project.read_bytes()
    _answer_with(monkeypatch, "y")

    def full_disk(_tasks: list[Task], _path: Path) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("task_tracker.cli.save", full_disk)

    exit_code = main(["delete", "2"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "disk full")
    assert project.read_bytes() == before


@pytest.mark.parametrize(
    ("deleted", "expected_ids", "new_id"),
    [(3, [1, 2, 3], 3), (2, [1, 3, 4], 4)],
    ids=["highest-reused", "gap-not-reused"],
)
def test_add_after_a_delete_numbers_the_new_task_from_the_highest_remaining_id(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    deleted: int,
    expected_ids: list[int],
    new_id: int,
):
    # Deleting the highest ID frees it for reuse; deleting a middle one leaves a gap
    # that `add` does not fill (D5). Only the gap case tells "highest + 1" from a
    # count: after deleting 2, a count gives 3 and collides with the stored task 3.
    _save_three(project)
    _answer_with(monkeypatch, "y")
    main(["delete", str(deleted)])

    exit_code = main(["add", "New"])

    stored = load(project)
    assert exit_code == 0
    assert [task.id for task in stored] == expected_ids
    assert (stored[-1].id, stored[-1].name) == (new_id, "New")


def test_a_script_can_answer_the_prompt_on_standard_input(tmp_path: Path):
    # `echo y | task-tracker delete 1`: the prompt reads standard input, so a script
    # does not need a `--yes` flag to delete a task, only an answer to read.
    save([Task(1, "Buy milk"), Task(2, "Walk dog")], tmp_path / "tasks.json")
    read_end, write_end = os.pipe()

    with _run_in_a_new_process(
        tmp_path, ["delete", "1"], write_end, stdin=subprocess.PIPE
    ) as child:
        os.close(write_end)
        assert child.stdin is not None
        child.stdin.write("y\n")
        child.stdin.close()
        child.wait(timeout=30)

    output = os.read(read_end, 4096).decode("utf-8")
    os.close(read_end)
    assert child.returncode == 0
    assert output == "Delete task 1: Buy milk? [y/N] Deleted task 1: Buy milk\n"
    assert (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8") == ""
    assert [task.id for task in load(tmp_path / "tasks.json")] == [2]


def test_delete_with_standard_output_closed_gives_one_error_line(tmp_path: Path):
    # With descriptor 1 closed, `sys.stdout` is None and `input` cannot prompt.
    save([Task(1, "Buy milk")], tmp_path / "tasks.json")
    before = (tmp_path / "tasks.json").read_bytes()

    with _run_in_a_new_process(
        tmp_path, ["delete", "1"], subprocess.DEVNULL, close_stdout=True
    ) as child:
        child.wait(timeout=30)

    error = (tmp_path / _ERRORS_FILE).read_text(encoding="utf-8")
    assert child.returncode == 1
    assert error.count("\n") == 1
    assert error.startswith("task-tracker: error: ")
    assert "Traceback" not in error
    assert (tmp_path / "tasks.json").read_bytes() == before


# --- M7: --global and --dir ---


def _global_list(home: Path) -> Path:
    return home / ".task-tracker" / "tasks.json"


def test_global_add_stores_the_task_under_the_home_directory(
    project: Path, home: Path, capsys: pytest.CaptureFixture[str]
):
    # Given a first run: the home directory has no `.task-tracker` yet
    assert not (home / ".task-tracker").exists()

    exit_code = main(["--global", "add", "Renew passport"])

    # Then the task is in the global list, and the project list was not touched
    assert exit_code == 0
    assert [(task.id, task.name) for task in load(_global_list(home))] == [
        (1, "Renew passport")
    ]
    assert not project.exists()
    assert "Added task 1: Renew passport" in capsys.readouterr().out


@pytest.mark.parametrize("flag", ["--global", "-g"])
def test_list_shows_only_the_list_it_was_asked_for(
    project: Path, home: Path, capsys: pytest.CaptureFixture[str], flag: str
):
    save([Task(1, "Project")], project)
    save([Task(1, "Global")], _global_list(home))

    main(["list"])
    project_names = _listed_names(capsys)
    main([flag, "list"])
    global_names = _listed_names(capsys)

    assert (project_names, global_names) == (["Project"], ["Global"])


def test_global_list_with_no_file_says_so_and_creates_nothing(
    home: Path, capsys: pytest.CaptureFixture[str]
):
    exit_code = main(["--global", "list"])

    assert exit_code == 0
    assert capsys.readouterr().out == f"No current tasks in {_global_list(home)}\n"
    assert not (home / ".task-tracker").exists()


@pytest.mark.parametrize("option", ["--global", "--dir PATH"])
def test_the_top_level_help_lists_the_location_options(
    capsys: pytest.CaptureFixture[str], option: str
):
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    assert option in capsys.readouterr().out


# The three ways to name a directory: both option spellings, and a relative path.
_DIRECTORY_FORMS = pytest.mark.parametrize(
    ("flag", "relative"),
    [("--dir", False), ("-d", False), ("-d", True)],
    ids=["long-absolute", "short-absolute", "short-relative"],
)


def _directory_argument(tmp_path: Path, name: str, *, relative: bool) -> str:
    return name if relative else str(tmp_path / name)


@_DIRECTORY_FORMS
def test_dir_stores_the_task_in_that_directory(
    project: Path, tmp_path: Path, flag: str, relative: bool
):
    groceries = tmp_path / "groceries"
    argument = _directory_argument(tmp_path, "groceries", relative=relative)

    exit_code = main([flag, argument, "add", "Milk"])

    assert exit_code == 0
    assert [task.name for task in load(groceries / "tasks.json")] == ["Milk"]
    assert not project.exists()


@_DIRECTORY_FORMS
def test_list_on_a_directory_that_does_not_exist_says_so_and_creates_nothing(
    project: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    flag: str,
    relative: bool,
):
    missing = tmp_path / "missing"
    argument = _directory_argument(tmp_path, "missing", relative=relative)

    exit_code = main([flag, argument, "list"])

    # The message names the absolute path, even for a relative option value.
    assert exit_code == 0
    assert capsys.readouterr().out == f"No current tasks in {missing / 'tasks.json'}\n"
    assert not missing.exists()
    assert not project.exists()


@pytest.mark.parametrize("command", [["list"], ["add", "Milk"]], ids=["list", "add"])
def test_dir_naming_a_regular_file_gives_one_error_line(
    project: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: list[str],
):
    # `load` and `save` both raise OSError for `plain/tasks.json`, which `main`
    # already turns into one line, so this needs no code of its own.
    plain = tmp_path / "plain"
    plain.write_text("not a directory", encoding="utf-8")

    exit_code = main(["--dir", str(plain), *command])

    assert exit_code == 1
    _assert_one_line_error(capsys, "plain")
    assert plain.read_text(encoding="utf-8") == "not a directory"
    assert not project.exists()


def test_dir_expands_a_leading_tilde_to_the_home_directory(
    project: Path, home: Path, tmp_path: Path
):
    # A shell leaves `~` alone in `--dir=~/groceries`, so the program gets the same
    # text for both spellings and must expand it, or it makes a directory named `~`.
    exit_code = main(["--dir", "~/groceries", "add", "Milk"])

    assert exit_code == 0
    assert [task.name for task in load(home / "groceries" / "tasks.json")] == ["Milk"]
    assert not (tmp_path / "~").exists()
    assert not project.exists()


def test_dir_with_a_tilde_that_cannot_be_expanded_is_a_bad_option_value(
    project: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    # `~name` for a user who does not exist: `expanduser` raises RuntimeError, which
    # argparse does not catch, so without a conversion this ends in a traceback.
    with pytest.raises(SystemExit) as exit_info:
        main(["--dir", "~no-such-user-m7/x", "list"])

    error = capsys.readouterr().err
    assert exit_info.value.code == 2
    assert "--dir" in error
    assert "~no-such-user-m7/x" in error
    assert list(tmp_path.iterdir()) == []


def test_an_empty_dir_is_a_bad_option_value(
    project: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    # `Path("")` is `Path(".")`, so `--dir "$PROJECT"` with PROJECT unset would
    # quietly use the list in the cwd.
    with pytest.raises(SystemExit) as exit_info:
        main(["--dir", "", "add", "Milk"])

    assert exit_info.value.code == 2
    assert "--dir" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "options",
    [
        ["--dir", "{dir}", "--global"],
        ["-d", "{dir}", "-g"],
        ["--global", "--dir", "{dir}"],
    ],
    ids=["long", "short", "reversed"],
)
def test_dir_together_with_global_is_refused_and_writes_nothing(
    project: Path,
    home: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    options: list[str],
):
    elsewhere = tmp_path / "elsewhere"
    argv = [option.replace("{dir}", str(elsewhere)) for option in options]

    with pytest.raises(SystemExit) as exit_info:
        main([*argv, "add", "Milk"])

    # argparse words the rest of the message differently for each order.
    assert exit_info.value.code == 2
    assert "not allowed with" in capsys.readouterr().err
    # No project file, no `elsewhere` directory, nothing under the fake home.
    assert list(tmp_path.iterdir()) == []
    assert list(home.iterdir()) == []


@pytest.mark.parametrize(
    "argv",
    [
        ["add", "Milk", "-d", "2026-11-02"],
        ["add", "Milk", "--global"],
        ["list", "--dir", "elsewhere"],
    ],
    ids=["slip-for-due", "global-after-command", "dir-after-command"],
)
def test_a_location_option_after_the_command_is_refused_and_creates_nothing(
    project: Path,
    home: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
):
    # `-d` and `-D` differ by one Shift. On the top-level parser a slip for `--due`
    # is an unrecognized argument; a subcommand that also took `-d` would bind
    # `2026-11-02` as a directory and create it on the first save.
    with pytest.raises(SystemExit) as exit_info:
        main(argv)

    assert exit_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []
    assert list(home.iterdir()) == []


def test_global_without_a_home_directory_gives_one_error_line(
    project: Path,
    home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    # `expanduser` returns its argument when it cannot expand, and `Path.home()` then
    # raises RuntimeError (HOME unset, and no password-file entry for the user, as in
    # a container started with an arbitrary user ID).
    monkeypatch.setattr("os.path.expanduser", lambda path: path)

    exit_code = main(["--global", "add", "Milk"])

    assert exit_code == 1
    _assert_one_line_error(capsys, "home directory")
    assert list(tmp_path.iterdir()) == []
    assert list(home.iterdir()) == []

"""The command line: argument parsing and the commands that use the task file."""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.storage import load, save
from task_tracker.task import Task, as_naive_datetime

# D2: the project list is `tasks.json` in the current directory.
_LIST_FILE = "tasks.json"


def _add(args: argparse.Namespace, path: Path) -> list[str]:
    """Store the new task and return the lines to show."""
    tasks = load(path)
    # D5: highest + 1, not a count, so a gap left by a delete is not reused.
    next_id = max((task.id for task in tasks), default=0) + 1
    task = Task(next_id, args.name, priority=args.priority, due=args.due)
    save([*tasks, task], path)
    return [f"Added task {task.id}: {task.name}"]


def _changes(args: argparse.Namespace) -> dict[str, Any]:
    """The keyword arguments for `Task.update`: only the options that were given."""
    given = {"name": args.name, "priority": args.priority, "status": args.status}
    changes = {name: value for name, value in given.items() if value is not None}
    # `due` is left out entirely when neither flag is given: in `Task.update` that
    # means "keep it", while `due=None` means "clear it".
    if args.due is not None:
        changes["due"] = args.due
    elif args.clear_due:
        changes["due"] = None
    return changes


_NOTHING_TO_UPDATE = (
    "nothing to update: give at least one of --name, --priority, --status, --due, "
    "--clear-due"
)


def _find(tasks: list[Task], task_id: int) -> Task:
    """Return the task with `task_id`, or refuse the command if there is none."""
    for task in tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"no task with ID {task_id}")


def _update(args: argparse.Namespace, path: Path) -> list[str]:
    """Change task `args.id` and return the line to show."""
    changes = _changes(args)
    # Refused before the file is read, so a command that changes nothing (a
    # forgotten or mistyped flag) cannot rewrite the file.
    if not changes:
        raise ValueError(_NOTHING_TO_UPDATE)
    tasks = load(path)
    task = _find(tasks, args.id)
    if not task.update(**changes):
        # Nothing to write: the file keeps its layout, and a concurrent command has
        # no window to lose (#27) for a command that changed nothing.
        return [f"No change to task {task.id}: {task.name}"]
    # Every other task is written back as it was read.
    save(tasks, path)
    return [f"Updated task {task.id}: {task.name}"]


_YES_ANSWERS = {"y", "yes"}
# What `input` raises when nothing can answer: EOFError when input ended,
# KeyboardInterrupt for Ctrl-C, and UnicodeDecodeError (a ValueError, so `main`
# would print a codec message without a word about the task) for an answer that is
# not valid text. A name, not a tuple in the `except`: ruff 0.16 drops the
# parentheses there (Python 3.14 allows that), and the older mypy and flake8 that
# CI runs reject the result.
_NO_ANSWER = (EOFError, KeyboardInterrupt, UnicodeDecodeError)


def _ask(prompt: str) -> str | None:
    """Show `prompt` and return the answer, or None when nothing can answer it.

    What the caller did not do about it is the caller's to say, so this only
    reports that there was no answer.
    """
    # `input` raises RuntimeError ("lost sys.stdin") when a standard stream was
    # closed at start-up. That is checked here and not caught: a RuntimeError from
    # anywhere else (RecursionError, NotImplementedError) is a bug, and should
    # stay one. `input` also looks at standard error, as it flushes it first.
    if sys.stdin is None or sys.stdout is None or sys.stderr is None:
        return None
    try:
        return input(_printable(prompt, sys.stdout))
    except _NO_ANSWER:
        # A terminal echoes `^C` or `^D` after the prompt and leaves the cursor
        # there, so the error would run on from it. It goes to standard error, where
        # the error goes, and is skipped when nobody is typing.
        if sys.stdin.isatty():
            _say("", sys.stderr)
        return None


def _delete(args: argparse.Namespace, path: Path) -> list[str]:
    """Ask about task `args.id`, delete it only on a yes, and return the line to show."""
    tasks = load(path)
    task = _find(tasks, args.id)
    answer = _ask(f"Delete task {task.id}: {task.name}? [y/N] ")
    if answer is None:
        raise ValueError(f"no answer to the prompt: task {task.id} was not deleted")
    if answer.strip().lower() not in _YES_ANSWERS:
        return [f"Kept task {task.id}: {task.name}"]
    # The prompt waits on a person, so the list read above may be stale. Read it
    # again, and delete only the task that was shown; the rest is saved as read now.
    tasks = load(path)
    if task not in tasks:
        raise ValueError(
            f"task {task.id} changed or was removed while the prompt was open: "
            "nothing was deleted"
        )
    save([other for other in tasks if other.id != task.id], path)
    return [f"Deleted task {task.id}: {task.name}"]


# Highest priority first. The rank is the enum's definition order, because the
# string values sort CRITICAL, HIGH, LOW, MEDIUM (Review Focus 1).
_PRIORITY_RANK = {priority: rank for rank, priority in enumerate(Priority)}
_STATUS_WIDTH = max(map(len, Status))
_PRIORITY_WIDTH = max(map(len, Priority))
# Every datetime prints as YYYY-MM-DDTHH:MM:SS (D6), 19 characters.
_DATETIME_WIDTH = 19


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


def _describe(task: Task) -> str:
    due = task.due.isoformat() if task.due else "-"
    return (
        f"{task.id:>4}  {task.status:<{_STATUS_WIDTH}}  "
        f"{task.priority:<{_PRIORITY_WIDTH}}  {due:<{_DATETIME_WIDTH}}  {task.name}"
    )


def _done_order(task: Task) -> tuple[datetime, int]:
    """Sort key for the done tasks: date completed, then ID (M4)."""
    # `Task` and `load` already refuse a DONE task without a date completed. This
    # says so again in every mode (`python -O` removes an assert), and tells pyright.
    if task.date_completed is None:
        raise ValueError(f"task {task.id} is DONE but has no date completed")
    return (task.date_completed, task.id)


def _list(args: argparse.Namespace, path: Path) -> list[str]:
    """Return the lines to show: the current tasks, then the done ones with `--all`."""
    tasks = load(path)
    current = [task for task in tasks if task.status is not Status.DONE]
    shown = sorted(current, key=_current_order)
    if args.include_done:
        done = [task for task in tasks if task.status is Status.DONE]
        shown += sorted(done, key=_done_order)
    if not shown:
        # Under `--all` the done tasks count too, so "current" would mislead.
        scope = "tasks" if args.include_done else "current tasks"
        return [f"No {scope} in {path}"]
    return [_describe(task) for task in shown]


# What is escaped, because it moves the cursor, sends commands to the terminal,
# splits one line into two, or reorders how the rest of a line is displayed:
# - the control characters (Unicode category Cc: C0, DEL and C1);
# - the line and paragraph separators (Zl, Zp);
# - the bidirectional marks, embeddings, overrides and isolates (Unicode Standard
#   Annex 9), which a name from a shared file could use to make a line read in
#   another order than it is stored.
# The first two groups equal the categories over every code point, and one scan of
# the line is an order of magnitude faster than a category lookup for each
# character. The zero-width joiner and the wide space are not here: they are text.
_UNSAFE = re.compile(
    r"[\x00-\x1f\x7f-\x9f"  # Cc
    r"\u2028\u2029"  # Zl, Zp
    r"\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]"  # bidirectional controls
)


def _escape(match: re.Match[str]) -> str:
    return match.group().encode("unicode_escape").decode("ascii")


def _printable(line: str, stream: TextIO) -> str:
    """Return `line` with what could break or drive the terminal shown as escapes.

    A name is whatever was typed or whatever a shared file carries (the README
    expects lists to be shared), so it is not printed raw: a newline would make one
    task two lines, and an escape sequence would reach the terminal. Anything that
    `stream` cannot encode becomes an escape too, so a listing is not stopped
    partway by a codec error. A literal backslash is left as it is, so it can look
    like an escape.
    """
    escaped = _UNSAFE.sub(_escape, line)
    encoding = stream.encoding or "utf-8"
    return escaped.encode(encoding, "backslashreplace").decode(encoding)


def _say(line: str, stream: TextIO | None) -> None:
    """Print one escaped line to `stream`, the only way the program writes text.

    Standard output and standard error both reach a terminal, and an error message
    can repeat text from the task file (a key in a record, for one), so both go
    through `_printable`. A closed stream is `None`, and `print(file=None)` would
    write to standard output instead, so it is skipped here.
    """
    if stream is None:
        return
    print(_printable(line, stream), file=stream)


def _discard_stdout() -> None:
    """Point standard output at devnull, so that nothing is left to flush again.

    A write that failed leaves its bytes in the buffer, and Python flushes stdout
    once more at exit. That flush fails the same way, prints "Exception ignored",
    and turns the exit code into 120. The retry succeeds against devnull (the
    recipe in the `signal` module's SIGPIPE note). The extra descriptor is closed
    once `dup2` has made its copy.
    """
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, sys.stdout.fileno())
    finally:
        os.close(devnull)


def _show(lines: list[str], prog: str) -> int:
    """Print `lines` and return the exit code.

    The commands only build their lines. Printing is here, outside the `try` in
    `main`, so a failure to write is never reported as a problem with the data,
    and `add` has already saved by the time it can happen.
    """
    if sys.stdout is None:
        # Descriptor 1 was closed when the program started (cron and some service
        # managers do this), so there is no stream. `print` itself treats that as
        # "nowhere to write"; the command has still done its work.
        return 0
    try:
        for line in lines:
            _say(line, sys.stdout)
        # A pipe buffers, so a reader that has gone shows up at the flush.
        sys.stdout.flush()
    except BrokenPipeError:
        # The reader stopped early, as `head` does. That is not worth a message.
        # The recipe in the `signal` module's SIGPIPE note also exits with 1.
        _discard_stdout()
        return 1
    except OSError as error:
        _discard_stdout()
        _say(f"{prog}: error: cannot write the output: {error}", sys.stderr)
        return 1
    return 0


def _due(text: str) -> datetime:
    """Read `--due`: a date, or a date and time, in local time (D6).

    The rule is the one `Task` applies to any date, so it is not repeated here.
    What this adds is the way a bad value is reported: every one raises the same
    `ArgumentTypeError`, so argparse names the flag and the expected form and
    exits with 2, a UTC offset included, where `Task` alone would give exit code 1.
    """
    try:
        due = as_naive_datetime("due", text)
    except ValueError:
        due = None
    # `None` is for the type checker: a text is never None.
    if due is None:
        raise argparse.ArgumentTypeError(
            f"expected YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS in local time, not {text!r}"
        )
    return due


def _task_id(text: str) -> int:
    """Read a task ID: ASCII digits, 1 or more, the form the task file holds.

    `int` alone also takes `+1`, `0_1`, a padded " 1 " and non-ASCII digits, and it
    lets `0` and `-1` through to a "no task" error, although a task never has an ID
    below 1 (`Task` refuses it). Every one of them is a bad value, as `1.5` is, so
    argparse names the argument and exits with 2.
    """
    if text.isascii() and text.isdecimal() and int(text) >= 1:
        return int(text)
    raise argparse.ArgumentTypeError(
        f"expected a whole number of 1 or more, not {text!r}"
    )


# Shared by `add` and `update`, so a change to what they accept is made once. The
# choices are plain strings, not `Priority` members: see the note in `_build_parser`.
_PRIORITIES = [priority.value for priority in Priority]
_DUE_OPTION: dict[str, Any] = {
    "type": _due,
    "metavar": "DATETIME",
    "help": "YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS, local time",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task-tracker")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="add a task")
    add.add_argument("name")
    # No `type=`: argparse converts before it checks `choices`, so a converter
    # would fail first with a message that lists nothing. The choices are plain
    # strings because argparse prints each one with `repr`, and `Task` turns the
    # checked string into a `Priority`.
    add.add_argument("--priority", "-p", choices=_PRIORITIES, default=Priority.LOW)
    add.add_argument("--due", "-D", **_DUE_OPTION)
    add.set_defaults(run=_add)
    listing = commands.add_parser(
        "list", help="list the current tasks (all tasks with --all)"
    )
    listing.add_argument(
        "--all",
        "-a",
        action="store_true",
        dest="include_done",
        help="also list the done tasks, after the current ones",
    )
    listing.set_defaults(run=_list)
    update = commands.add_parser("update", help="change a stored task")
    update.add_argument("id", type=_task_id, help="ID of the task to change")
    # Defaults are `None` so that a missing option is told apart from one given
    # with the default value. As in `add`, no `type=`: argparse would convert before
    # it checks `choices`.
    update.add_argument("--name", "-n", help="new name")
    update.add_argument(
        "--priority",
        "-p",
        choices=_PRIORITIES,
        help="new priority",
    )
    update.add_argument(
        "--status",
        "-s",
        choices=[status.value for status in Status],
        help="new status (DONE sets the date completed, leaving DONE clears it)",
    )
    # Mutually exclusive: a date and "no date" in one command contradict each other.
    due = update.add_mutually_exclusive_group()
    due.add_argument("--due", "-D", **_DUE_OPTION)
    due.add_argument(
        "--clear-due",
        "-C",
        action="store_true",
        help="remove the due date (cannot be used with --due)",
    )
    update.set_defaults(run=_update)
    delete = commands.add_parser("delete", help="delete a task, after asking")
    delete.add_argument("id", type=_task_id, help="ID of the task to delete")
    delete.set_defaults(run=_delete)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command in `argv` (the process arguments by default).

    The return value is the exit code: the console script passes it to
    `sys.exit`. A bad option value exits 2 inside argparse. Anything else that
    goes wrong at runtime prints one line to standard error and returns 1, and so
    does a reader that closes the pipe early, quietly.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        lines = args.run(args, Path.cwd() / _LIST_FILE)
    except (ValueError, OSError) as error:
        # `Task` and `load` raise ValueError for a blank name or a corrupt file
        # (M2 made it the one type); OSError is a file that cannot be read or written.
        _say(f"{parser.prog}: error: {error}", sys.stderr)
        return 1
    return _show(lines, parser.prog)

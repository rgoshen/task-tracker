"""The command line: argument parsing and the commands that use the task file."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from task_tracker.priority import Priority
from task_tracker.status import Status
from task_tracker.storage import load, save
from task_tracker.task import Task

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


def _list(_args: argparse.Namespace, path: Path) -> list[str]:
    """Return the lines to show: the current tasks, or that there are none."""
    current = [task for task in load(path) if task.status is not Status.DONE]
    if not current:
        return [f"No current tasks in {path}"]
    return [_describe(task) for task in sorted(current, key=_current_order)]


def _show(lines: list[str], prog: str) -> int:
    """Print `lines` and return the exit code.

    The commands only build their lines. Printing is here, outside the `try` in
    `main`, so a failure to write is never reported as a problem with the data,
    and `add` has already saved by the time it can happen.
    """
    try:
        for line in lines:
            print(line)
        # A pipe buffers, so a reader that has gone shows up at the flush.
        sys.stdout.flush()
    except BrokenPipeError:
        # The reader stopped early, as `head` does. That is not worth a message.
        # Python flushes stdout once more at exit and would fail the same way, so
        # point it at devnull first (the recipe in the `signal` module's SIGPIPE
        # note, which also exits with 1).
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1
    except OSError as error:
        print(f"{prog}: error: cannot write the output: {error}", file=sys.stderr)
        return 1
    return 0


def _due(text: str) -> datetime:
    """Read `--due`: a date, or a date and time, in local time (D6).

    Every bad value raises the same `ArgumentTypeError`, so argparse reports it
    the same way: the flag, the expected form, and exit code 2. A UTC offset
    parses but is not local time, so it is a bad value here too, not an error
    that `Task` raises later with an exit code of 1.
    """
    try:
        due = datetime.fromisoformat(text)
    except ValueError:
        due = None
    if due is None or due.tzinfo is not None:
        raise argparse.ArgumentTypeError(
            f"expected YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS in local time, not {text!r}"
        )
    return due


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task-tracker")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="add a task")
    add.add_argument("name")
    # No `type=`: argparse converts before it checks `choices`, so a converter
    # would fail first with a message that lists nothing. The choices are plain
    # strings because argparse prints each one with `repr`, and `Task` turns the
    # checked string into a `Priority`.
    add.add_argument(
        "--priority",
        "-p",
        choices=[priority.value for priority in Priority],
        default=Priority.LOW,
    )
    add.add_argument(
        "--due",
        "-D",
        type=_due,
        metavar="DATETIME",
        help="YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS, local time",
    )
    add.set_defaults(run=_add)
    commands.add_parser("list", help="list the current tasks").set_defaults(run=_list)
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
        print(f"{parser.prog}: error: {error}", file=sys.stderr)
        return 1
    return _show(lines, parser.prog)

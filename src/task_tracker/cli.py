"""The command line: argument parsing and the commands that use the task file."""

import argparse
from datetime import datetime
from pathlib import Path

from task_tracker.priority import Priority
from task_tracker.storage import load, save
from task_tracker.task import Task

# D2: the project list is `tasks.json` in the current directory.
_LIST_FILE = "tasks.json"


def _add(args: argparse.Namespace, path: Path) -> None:
    tasks = load(path)
    # D5: highest + 1, not a count, so a gap left by a delete is not reused.
    next_id = max((task.id for task in tasks), default=0) + 1
    task = Task(next_id, args.name, priority=args.priority, due=args.due)
    save([*tasks, task], path)
    print(f"Added task {task.id}: {task.name}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task-tracker")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="add a task")
    add.add_argument("name")
    add.add_argument(
        "--priority",
        "-p",
        type=Priority,
        choices=list(Priority),
        default=Priority.LOW,
    )
    add.add_argument(
        "--due",
        "-D",
        type=datetime.fromisoformat,
        metavar="DATETIME",
        help="YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS, local time",
    )
    add.set_defaults(run=_add)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command in `argv` (the process arguments by default).

    The return value is the exit code: the console script passes it to
    `sys.exit`.
    """
    args = _build_parser().parse_args(argv)
    args.run(args, Path.cwd() / _LIST_FILE)
    return 0

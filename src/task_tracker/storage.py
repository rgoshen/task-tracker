"""Saving tasks to a JSON file and loading them back."""

import json
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from typing import Any

from task_tracker.task import Task


def _to_record(task: Task) -> dict[str, Any]:
    return {
        field.name: _to_json_value(getattr(task, field.name)) for field in fields(task)
    }


def _to_json_value(value: object) -> object:
    # The enums are `StrEnum`s, so JSON already writes their labels.
    return value.isoformat() if isinstance(value, datetime) else value


def load(path: Path) -> list[Task]:
    """Read the tasks in `path`. A file that does not exist is an empty list."""
    try:
        with path.open(encoding="utf-8") as file:
            records = json.load(file)
    except FileNotFoundError:
        return []
    return [Task.restore(**record) for record in records]


def save(tasks: list[Task], path: Path) -> None:
    """Write `tasks` to `path`, creating the directories above it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump([_to_record(task) for task in tasks], file, indent=2)
        file.write("\n")

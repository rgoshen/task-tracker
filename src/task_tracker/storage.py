"""Saving tasks to a JSON file and loading them back."""

import json
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from typing import Any

from task_tracker.task import Task

_FIELD_NAMES = {field.name for field in fields(Task)}


def _to_record(task: Task) -> dict[str, Any]:
    return {
        field.name: _to_json_value(getattr(task, field.name)) for field in fields(task)
    }


def _to_json_value(value: object) -> object:
    # The enums are `StrEnum`s, so JSON already writes their labels.
    return value.isoformat() if isinstance(value, datetime) else value


def _read_records(path: Path) -> list[Any]:
    try:
        with path.open(encoding="utf-8") as file:
            records = json.load(file)
    except ValueError as error:
        # JSONDecodeError and UnicodeDecodeError are both ValueErrors.
        raise ValueError(f"{path}: not valid JSON: {error}") from error
    # ValueError, not TypeError: M3's CLI catches one type for a bad file.
    if not isinstance(records, list):
        raise ValueError(f"{path}: must hold a list of tasks")  # noqa: TRY004
    return records


def _from_record(record: object) -> Task:
    if not isinstance(record, dict):
        raise ValueError("must be an object")  # noqa: TRY004
    missing = _FIELD_NAMES - record.keys()
    if missing:
        raise ValueError(f"missing field(s): {', '.join(sorted(missing))}")
    unknown = record.keys() - _FIELD_NAMES
    if unknown:
        # Ignoring a field would delete it on the next save, which rewrites the file.
        raise ValueError(f"unknown field(s): {', '.join(sorted(unknown))}")
    return Task.restore(**record)


def load(path: Path) -> list[Task]:
    """Read the tasks in `path`. A file that does not exist is an empty list.

    A file whose content is wrong raises `ValueError` naming the file and, for a
    bad task, its position. Any other failure to read it is left as it is.
    """
    try:
        records = _read_records(path)
    except FileNotFoundError:
        return []
    tasks: list[Task] = []
    seen_ids: set[int] = set()
    for position, record in enumerate(records, start=1):
        try:
            task = _from_record(record)
            if task.id in seen_ids:
                raise ValueError(f"duplicate id {task.id}")
        except ValueError as error:
            raise ValueError(f"{path}: record {position}: {error}") from error
        seen_ids.add(task.id)
        tasks.append(task)
    return tasks


def save(tasks: list[Task], path: Path) -> None:
    """Write `tasks` to `path`, creating the directories above it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump([_to_record(task) for task in tasks], file, indent=2)
        file.write("\n")

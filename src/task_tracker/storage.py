"""Saving tasks to a JSON file and loading them back."""

import json
import os
import tempfile
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
    return Task.restore(**record)


def _restore_all(records: list[Any], path: Path) -> list[Task]:
    """Rebuild every task, enforcing the rules a file must meet.

    `load` applies them to what it read and `save` to what it is about to write,
    so a file this module writes is one it can read back.
    """
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


def load(path: Path) -> list[Task]:
    """Read the tasks in `path`. A file that does not exist is an empty list.

    A file whose content is wrong raises `ValueError` naming the file and, for a
    bad task, its position. Any other failure to read it is left as it is.
    """
    try:
        records = _read_records(path)
    except FileNotFoundError:
        return []
    return _restore_all(records, path)


def save(tasks: list[Task], path: Path) -> None:
    """Write `tasks` to `path`, creating the directories above it.

    Tasks that `load` would reject raise `ValueError` before anything is written.
    The file is replaced in one step, so a failure partway leaves the previous
    file as it was and no temporary file behind.
    """
    records = [_to_record(task) for task in tasks]
    # The file being replaced is the last good state. Refuse a list that load would
    # reject (a duplicate ID, or a field changed after construction) before any
    # directory or temporary file exists.
    _restore_all(records, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Next to the target, not in the system temp directory: os.replace is atomic
    # only within one filesystem and may fail across two.
    file_descriptor, name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temp_path = Path(name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)
            file.write("\n")
            # ponytail: no flush and fsync before the replace, so a power cut right
            # after a save can still leave the old or an empty file. Add
            # file.flush() and os.fsync(file.fileno()) if that ever matters.
        os.replace(temp_path, path)
    finally:
        # Gone already after a successful replace; this removes it after a failure.
        temp_path.unlink(missing_ok=True)
